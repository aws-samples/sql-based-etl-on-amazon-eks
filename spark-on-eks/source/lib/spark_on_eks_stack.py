# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from aws_cdk import (
    core, 
    aws_eks as eks,
    aws_secretsmanager as secmger
)
from bin.network_sg import NetworkSgConst
from bin.iam_roles import IamConst
from bin.eks_cluster import EksConst
from bin.eks_service_account import EksSAConst
from bin.eks_base_app import EksBaseAppConst
from bin.s3_app_code import S3AppCodeConst
from bin.spark_permission import SparkOnEksSAConst
from lib.cloud_front_stack import NestedStack
from bin.manifest_reader import *
import json

class SparkOnEksStack(core.Stack):

    @property
    def code_bucket(self):
        return self.app_s3.code_bucket

    @property
    def argo_url(self):
        return self._argo_alb.value

    @property
    def jhub_url(self):
        return self._jhub_alb.value

    def __init__(self, scope: core.Construct, id: str, eksname: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Cloudformation input params
        datalake_bucket = core.CfnParameter(self, "datalakebucket", type="String",
            description="Your existing S3 bucket to be accessed by Jupyter Notebook and ETL job. Default: blank",
            default=""
        )
        login_name = core.CfnParameter(self, "jhubuser", type="String",
            description="Your username login to jupyter hub",
            default="sparkoneks"
        )

        # Auto-generate a user login in secrets manager
        jhub_secret = secmger.Secret(self, 'jHubPwd', 
            generate_secret_string=secmger.SecretStringGenerator(
                exclude_punctuation=True,
                secret_string_template=json.dumps({'username': login_name.value_as_string}),
                generate_string_key="password")
        )

        # A new bucket to store app code and access logs
        self.app_s3 = S3AppCodeConst(self,'appcode')

        # 1. Setup EKS base infrastructure
        network_sg = NetworkSgConst(self,'network-sg', eksname, self.app_s3.code_bucket)
        iam = IamConst(self,'iam_roles', eksname)
        eks_cluster = EksConst(self,'eks_cluster', eksname, network_sg.vpc, iam.managed_node_role, iam.admin_role, self.region)
        eks_security = EksSAConst(self, 'eks_sa', eks_cluster.my_cluster, jhub_secret)
        eks_base_app = EksBaseAppConst(self, 'eks_base_app', eks_cluster.my_cluster, self.region)

        # 2. Setup Spark application access control
        app_security = SparkOnEksSAConst(self,'spark_service_account', 
            eks_cluster.my_cluster, 
            login_name.value_as_string,
            self.app_s3.code_bucket,
            datalake_bucket.value_as_string
        )
        
        # 3. Install ETL orchestrator - Argo
        # can be replaced by other workflow tool, ie. Airflow
        argo_install = eks_cluster.my_cluster.add_helm_chart('ARGOChart',
            chart='argo',
            repository='https://argoproj.github.io/argo-helm',
            release='argo',
            namespace='argo',
            create_namespace=True,
            values=loadYamlLocal('../app_resources/argo-values.yaml')
        )
        # Create a Spark workflow template with different T-shirt size
        submit_tmpl = eks_cluster.my_cluster.add_manifest('SubmitSparkWrktmpl',
            loadYamlLocal('../app_resources/spark-template.yaml')
        )
        submit_tmpl.node.add_dependency(argo_install)

        # 4. Install Arc Jupyter notebook to as Spark ETL IDE
        jhub_install= eks_cluster.my_cluster.add_helm_chart('JHubChart',
            chart='jupyterhub',
            repository='https://jupyterhub.github.io/helm-chart',
            release='jhub',
            version='0.11.1',
            namespace='jupyter',
            create_namespace=False,
            values=loadYamlReplaceVarLocal('../app_resources/jupyter-values.yaml', 
                fields={
                    "{{codeBucket}}": self.app_s3.code_bucket,
                    "{{region}}": self.region 
                })
        )

        # get Arc Jupyter login from secrets manager
        name_parts= core.Fn.split('-',jhub_secret.secret_name)
        name_no_suffix=core.Fn.join('-',[core.Fn.select(0, name_parts), core.Fn.select(1, name_parts)])

        config_hub = eks.KubernetesManifest(self,'JHubConfig',
            cluster=eks_cluster.my_cluster,
            manifest=loadYamlReplaceVarLocal('../app_resources/jupyter-config.yaml', 
                fields= {
                    "{{MY_SA}}": app_security.jupyter_sa,
                    "{{REGION}}": self.region, 
                    "{{SECRET_NAME}}": name_no_suffix
                }, 
                multi_resource=True)
        )
        config_hub.node.add_dependency(jhub_install)
   
        # 5.(OPTIONAL) retrieve ALB DNS Name to enable Cloudfront in the following nested stack.
        # Recommend to remove this section and the rest of CloudFront component. 
        # Setup your own certificate then add to ALB, to enable the HTTPS.
        self._argo_alb = eks.KubernetesObjectValue(self, 'argoALB',
            cluster=eks_cluster.my_cluster,
            json_path='.status.loadBalancer.ingress[0].hostname',
            object_type='ingress',
            object_name='argo-server',
            object_namespace='argo'
        )
        self._argo_alb.node.add_dependency(argo_install)

        self._jhub_alb=eks.KubernetesObjectValue(self, 'jhubALB',
            cluster=eks_cluster.my_cluster,
            json_path='.status.loadBalancer.ingress[0].hostname',
            object_type='ingress',
            object_name='jupyterhub',
            object_namespace='jupyter'
        )
        self._jhub_alb.node.add_dependency(config_hub)
