# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_s3 as s3
)
class NetworkSgConst(core.Construct):

    @property
    def vpc(self):
        return self._vpc
        
    # @property
    # def efs_sg(self):
    #     return self._eks_efs_sg


    def __init__(self,scope: core.Construct, id:str, eksname:str, codebucket: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # //*************************************************//
        # //******************* NETWORK ********************//
        # //************************************************//
        # create VPC
        self._vpc = ec2.Vpc(self, 'eksVpc',max_azs=2)
        core.Tags.of(self._vpc).add('Name', eksname + 'EksVpc')

        self._log_bucket=s3.Bucket.from_bucket_name(self,'vpc_logbucket', codebucket)
        self._vpc.add_flow_log("FlowLogCloudWatch",
            destination=ec2.FlowLogDestination.to_s3(self._log_bucket,'vpcRejectlog/'),
            traffic_type=ec2.FlowLogTrafficType.REJECT
        )
        # VPC endpoint security group
        self._vpc_endpoint_sg = ec2.SecurityGroup(self,'EndpointSg',
            security_group_name='SparkOnEKS-VPCEndpointSg',
            vpc=self._vpc,
            description='Security Group for Endpoint',
        )
        self._vpc_endpoint_sg.add_ingress_rule(ec2.Peer.ipv4(self._vpc.vpc_cidr_block),ec2.Port.tcp(port=443))
        core.Tags.of(self._vpc_endpoint_sg).add('Name','SparkOnEKS-VPCEndpointSg')

        # Add VPC endpoint 
        self._vpc.add_gateway_endpoint("S3GatewayEndpoint",
                                        service=ec2.GatewayVpcEndpointAwsService.S3,
                                        subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                                 ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE)])
                                                 
        # self._vpc.add_interface_endpoint("EcrDockerEndpoint",service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER, security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("CWLogsEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("AthenaEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ATHENA,security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("KMSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.KMS,security_groups=[self._vpc_endpoint_sg])
        # //******************************************************//
        # //******************* SECURITY GROUP ******************//
        # //****************************************************//
        # EFS SG
        # self._eks_efs_sg = ec2.SecurityGroup(self,'EFSSg',
        #     security_group_name=eksname + '-EFS-sg',
        #     vpc=self._vpc,
        #     description='NFS access to EFS from EKS worker nodes',
        # )
        # self._eks_efs_sg.add_ingress_rule(ec2.Peer.ipv4(self._vpc.vpc_cidr_block),ec2.Port.tcp(port=2049))

        # core.Tags.of(self._eks_efs_sg).add('kubernetes.io/cluster/' + eksname,'owned')
        # core.Tags.of(self._eks_efs_sg).add('Name', eksname+'-EFS-sg')
    