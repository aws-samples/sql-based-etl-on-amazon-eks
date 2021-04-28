# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
from aws_cdk import (
    core,
    aws_efs as efs,
    aws_ec2 as ec2
)
from aws_cdk.aws_eks import ICluster, KubernetesManifest
from lib.util.manifest_reader import *
import os

class EksBaseAppConst(core.Construct):
    def __init__(self,scope: core.Construct, id: str, eks_cluster: ICluster, region: str, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

        source_dir=os.path.split(os.environ['VIRTUAL_ENV'])[0]+'/source'
        # Add Cluster Autoscaler to EKS
        _var_mapping = {
            "{{region_name}}": region, 
            "{{cluster_name}}": eks_cluster.cluster_name, 
        }
        _scaler_chart = eks_cluster.add_helm_chart('ClusterAutoScaler',
            chart='cluster-autoscaler-chart',
            repository='https://kubernetes.github.io/autoscaler',
            release='nodescaler',
            create_namespace=False,
            namespace='kube-system',
            values=loadYamlReplaceVarLocal(source_dir+'/app_resources/autoscaler-values.yaml',_var_mapping)
        )

        # Add container insight (CloudWatch Log) to EKS
        _cw_log = KubernetesManifest(self,'ContainerInsight',
            cluster=eks_cluster, 
            manifest=loadYamlReplaceVarRemotely('https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml', 
                    fields=_var_mapping,
                    multi_resource=True
            )
        )

        # Add ALB ingress controller to EKS
        _alb_chart = eks_cluster.add_helm_chart('ALBChart',
            chart='aws-load-balancer-controller',
            repository='https://aws.github.io/eks-charts',
            release='alb',
            create_namespace=False,
            namespace='kube-system',
            values=loadYamlReplaceVarLocal(source_dir+'/app_resources/alb-values.yaml',
                fields={
                    "{{region_name}}": region, 
                    "{{cluster_name}}": eks_cluster.cluster_name, 
                    "{{vpc_id}}": eks_cluster.vpc.vpc_id
                }
            )
        )

        # Add external secrets controller to EKS
        _secret_chart = eks_cluster.add_helm_chart('SecretContrChart',
            chart='kubernetes-external-secrets',
            repository='https://external-secrets.github.io/kubernetes-external-secrets/',
            release='external-secrets',
            create_namespace=False,
            namespace='kube-system',
            values=loadYamlReplaceVarLocal(source_dir+'/app_resources/ex-secret-values.yaml',
                fields={
                    '{{region_name}}': region
                }
            )
        )

        # Add Spark Operator to EKS
        _spark_operator_chart = eks_cluster.add_helm_chart('SparkOperatorChart',
            chart='spark-operator',
            repository='https://googlecloudplatform.github.io/spark-on-k8s-operator',
            release='spark-operator',
            create_namespace=True,
            namespace='spark-operator',
            values=loadYamlReplaceVarLocal(source_dir+'/app_resources/spark-operator-values.yaml',fields={'':''})
        )

        # # Add Metric Server for Horizontal Pod Autoscaller
        # _hpa = KubernetesManifest(self,'PodAutoscaller',
        #     cluster=eks_cluster, 
        #     manifest=loadYamlReplaceVarRemotely('https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml', 
        #             fields=_var_mapping,
        #             multi_resource=True
        #     )
        # )

        # # Add EFS persistent storage to EKS across AZs
        # eks_cluster.add_helm_chart('EFSDriver', 
        #     chart='aws-efs-csi-driver',
        #     release='efs-driver',
        #     repository='https://kubernetes-sigs.github.io/aws-efs-csi-driver/',
        #     create_namespace=False,
        #     namespace='kube-system',
        # )
        # _k8s_efs = efs.FileSystem(self,'EFSFileSystem',
        #     vpc=eks_cluster.vpc,
        #     security_group=efs_sg,
        #     encrypted=True,
        #     lifecycle_policy=efs.LifecyclePolicy.AFTER_7_DAYS,
        #     performance_mode=efs.PerformanceMode.MAX_IO,
        #     removal_policy=core.RemovalPolicy.DESTROY,
        #     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE, one_per_az=True)
        # )
        # _pv= KubernetesManifest(self,'pvClaim',
        #     cluster=eks_cluster,
        #     manifest=loadYamlReplaceVarLocal('../app_resources/efs-spec.yaml', 
        #         fields= {
        #             "{{FileSystemId}} ": _k8s_efs.file_system_id
        #         },
        #         multi_resource=True)
        # )      
        # _pv.node.add_dependency(_k8s_efs)