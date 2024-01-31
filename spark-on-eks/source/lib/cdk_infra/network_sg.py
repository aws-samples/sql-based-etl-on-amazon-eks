# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from aws_cdk import (Tags, aws_ec2 as ec2)
from constructs import Construct
import lib.util.get_aws_managed_prefix as custom

class NetworkSgConst(Construct):

    @property
    def vpc(self):
        return self._vpc

    @property
    def alb_jhub_sg(self):
        return self._alb_jhub_sg
    @property
    def alb_argo_sg(self):
        return self._alb_argo_sg

    # @property
    # def efs_sg(self):
    #     return self._eks_efs_sg


    def __init__(self,scope: Construct, id:str, eksname:str, codebucket: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # //*************************************************//
        # //******************* NETWORK ********************//
        # //************************************************//
        # create VPC
        self._vpc = ec2.Vpc(self, 'eksVpc',max_azs=2, nat_gateways=1)
        Tags.of(self._vpc).add('Name', eksname + 'EksVpc')

        # ALB security group for Jupyter & Argo
        prefixlist_peer=ec2.Peer.prefix_list(
                custom.AwsManagedPrefixList(self,'cr-getprefixId',
                    custom.AwsManagedPrefixListProps(name='com.amazonaws.global.cloudfront.origin-facing')
                ).prefixlist_id
            )
        self._alb_jhub_sg=ec2.SecurityGroup(self,'JupyterALBInboundSG', vpc=self._vpc,description='Security Group for Jupyter ALB')
        self._alb_argo_sg=ec2.SecurityGroup(self,'ArgoALBInboundSG', vpc=self._vpc,description='Security Group for Argo ALB')
        self._alb_jhub_sg.add_ingress_rule(prefixlist_peer,ec2.Port.tcp(port=80))
        self._alb_argo_sg.add_ingress_rule(prefixlist_peer,ec2.Port.tcp(port=2746))
        Tags.of(self._alb_jhub_sg).add('Name','SparkOnEKS-JhubSg')
        Tags.of(self._alb_argo_sg).add('Name','SparkOnEKS-ArgoSg')

        # VPC endpoint security group
        self._vpc_endpoint_sg = ec2.SecurityGroup(self,'EndpointSg',
            vpc=self._vpc,
            description='Security Group for Endpoint',
        )
        self._vpc_endpoint_sg.add_ingress_rule(ec2.Peer.ipv4(self._vpc.vpc_cidr_block),ec2.Port.tcp(port=443))
        Tags.of(self._vpc_endpoint_sg).add('Name','SparkOnEKS-VPCEndpointSg')

        # Add VPC endpoint 
        self._vpc.add_gateway_endpoint("S3GatewayEndpoint",
                                        service=ec2.GatewayVpcEndpointAwsService.S3,
                                        subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                                 ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)])
                                                 
        # self._vpc.add_interface_endpoint("EcrDockerEndpoint",service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER, security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("CWLogsEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("AthenaEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ATHENA,security_groups=[self._vpc_endpoint_sg])
        self._vpc.add_interface_endpoint("KMSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.KMS,security_groups=[self._vpc_endpoint_sg])