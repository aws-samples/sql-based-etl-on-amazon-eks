# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from aws_cdk import (Stack, Duration, RemovalPolicy, Aws, Fn, CfnParameter, aws_eks as eks,aws_secretsmanager as secmger,aws_kms as kms)
from constructs import Construct
from lib.cdk_infra.network_sg import NetworkSgConst
from lib.cdk_infra.iam_roles import IamConst
from lib.cdk_infra.eks_cluster import EksConst
from lib.cdk_infra.eks_service_account import EksSAConst
from lib.cdk_infra.eks_base_app import EksBaseAppConst
from lib.cdk_infra.s3_app_code import S3AppCodeConst
from lib.cdk_infra.spark_permission import SparkOnEksSAConst
from lib.util.manifest_reader import *
import json,os

class SparkOnEksStack(Stack):

    @property
    def code_bucket(self):
        return self.app_s3.code_bucket

    @property
    def argo_url(self):
        return self._argo_alb.value

    @property
    def jhub_url(self):
        return self._jhub_alb.value

    def __init__(self, scope: Construct, id: str, eksname: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        source_dir=os.path.split(os.environ['VIRTUAL_ENV'])[0]+'/source'

        # Cloudformation input params
        datalake_bucket = CfnParameter(self, "datalakebucket", type="String",
            description="Your existing S3 bucket to be accessed by Jupyter Notebook and ETL job. Default: blank",
            default=""
        )
        login_name="sparkoneks"
        # login_name = CfnParameter(self, "jhubuser", type="String",
        #     description="Your username login to jupyter hub.",
        #     default="sparkoneks"
        # )

        # Auto-generate a user login in secrets manager
        key = kms.Key(self, 'KMSKey',removal_policy=RemovalPolicy.DESTROY,enable_key_rotation=True)
        key.add_alias("alias/secretsManager")
        jhub_secret = secmger.Secret(self, 'jHubPwd', 
            generate_secret_string=secmger.SecretStringGenerator(
                exclude_punctuation=True,
                secret_string_template=json.dumps({'username': login_name}),
                # secret_string_template=json.dumps({'username': login_name.value_as_string}),
                generate_string_key="password"),
            removal_policy=RemovalPolicy.DESTROY,
            encryption_key=key
        )

        # A new bucket to store app code and access logs
        self.app_s3 = S3AppCodeConst(self,'appcode')

        # 1. Setup EKS base infrastructure
        network_sg = NetworkSgConst(self,'network-sg', eksname, self.app_s3.code_bucket)
        iam = IamConst(self,'iam_roles', eksname)
        eks_cluster = EksConst(self,'eks_cluster', eksname, network_sg.vpc, iam.managed_node_role, iam.admin_role)
        EksSAConst(self, 'eks_sa', eks_cluster.my_cluster, jhub_secret)
        base_app=EksBaseAppConst(self, 'eks_base_app', eks_cluster.my_cluster)

        # 2. Setup Spark application access control
        app_security = SparkOnEksSAConst(self,'spark_service_account', 
            eks_cluster.my_cluster, 
            login_name,
            # login_name.value_as_string,
            self.app_s3.code_bucket,
            datalake_bucket.value_as_string
        )
        app_security.node.add_dependency(base_app.secret_created)
        # 3. Install Arc Jupyter notebook to as Spark ETL IDE
        jhub_install= eks_cluster.my_cluster.add_helm_chart('JHubChart',
            chart='jupyterhub',
            repository='https://jupyterhub.github.io/helm-chart',
            release='jupyterhub',
            version='1.2.0',
            namespace='jupyter',
            create_namespace=False,
            values=load_yaml_replace_var_local(source_dir+'/app_resources/jupyter-values.yaml', 
                fields={
                    "{{codeBucket}}": self.app_s3.code_bucket,
                    "{{region}}": Aws.REGION
                })
        )
        jhub_install.node.add_dependency(app_security)

        # get Arc Jupyter login from secrets manager
        name_parts= Fn.split('-',jhub_secret.secret_name)
        name_no_suffix=Fn.join('-',[Fn.select(0, name_parts), Fn.select(1, name_parts)])
        config_hub = eks.KubernetesManifest(self,'JHubConfig',
            cluster=eks_cluster.my_cluster,
            manifest=load_yaml_replace_var_local(source_dir+'/app_resources/jupyter-config.yaml', 
                fields= {
                    "{{MY_SA}}": app_security.jupyter_sa,
                    "{{REGION}}": Aws.REGION, 
                    "{{SECRET_NAME}}": name_no_suffix
                }, 
                multi_resource=True)
        )
        config_hub.node.add_dependency(jhub_install)

        # 4. Install ETL orchestrator - Argo
        # can be replaced by other workflow tool, ie. Airflow
        argo_install = eks_cluster.my_cluster.add_helm_chart('ARGOChart',
            chart='argo-workflows',
            repository='https://argoproj.github.io/argo-helm',
            release='argo',
            version='0.1.4',
            namespace='argo',
            create_namespace=True,
            values=load_yaml_local(source_dir+'/app_resources/argo-values.yaml')
        )
        argo_install.node.add_dependency(config_hub)
        # Create a Spark workflow template with different T-shirt size
        submit_tmpl = eks_cluster.my_cluster.add_manifest('SubmitSparkWrktmpl',
            load_yaml_local(source_dir+'/app_resources/spark-template.yaml')
        )
        submit_tmpl.node.add_dependency(argo_install)
   
        # 5.(OPTIONAL) retrieve ALB DNS Name to enable Cloudfront in the following nested stack.
        # Recommend to remove the CloudFront component
        # Setup your TLS certificate with your own domain name.
        self._jhub_alb=eks.KubernetesObjectValue(self, 'jhubALB',
            cluster=eks_cluster.my_cluster,
            json_path='..status.loadBalancer.ingress[0].hostname',
            object_type='ingress.networking',
            object_name='jupyterhub',
            object_namespace='jupyter',
            timeout=Duration.minutes(10)
        )
        self._jhub_alb.node.add_dependency(config_hub)
        self._argo_alb = eks.KubernetesObjectValue(self, 'argoALB',
            cluster=eks_cluster.my_cluster,
            json_path='..status.loadBalancer.ingress[0].hostname',
            object_type='ingress.networking',
            object_name='argo-argo-workflows-server',
            object_namespace='argo',
            timeout=Duration.minutes(10)
        )
        self._argo_alb.node.add_dependency(argo_install)

