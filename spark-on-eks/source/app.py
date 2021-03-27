# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3
from aws_cdk import core
# from bin.config import ConfigSectionMap
from lib.spark_on_eks_stack import SparkOnEksStack
from lib.cloud_front_stack import NestedStack
from os import environ

app = core.App()

# Get environment vars from deployment/enviornment.cfg file, run 'cdk synth -c env=develop'

# target_env = app.node.try_get_context('env')
# account = ConfigSectionMap(target_env)['account']
# region = ConfigSectionMap(target_env)['region']
# env = core.Environment(account=account, region=region)
eks_name = app.node.try_get_context('cluster_name') ## + '-' + ConfigSectionMap(target_env)['env_str']
env=core.Environment(account=environ.get("CDK_DEPLOY_ACCOUNT", environ["CDK_DEFAULT_ACCOUNT"]),
                    region=environ.get("AWS_REGION", environ["CDK_DEFAULT_REGION"]))

# Spin up the main stack
eks_stack = SparkOnEksStack(app, 'SparkOnEKS', eks_name, env=env)
# Recommend to remove the CloudFront stack. Setup your own SSL certificate and add it to ALB.
cf_nested_stack = NestedStack(eks_stack,'CreateCloudFront', eks_stack.code_bucket, eks_name, eks_stack.argo_url, eks_stack.jhub_url)

core.Tags.of(eks_stack).add('project', 'sqlbasedetl')
core.Tags.of(cf_nested_stack).add('project', 'sqlbasedetl')

# Deployment Output
core.CfnOutput(eks_stack,'CODE_BUCKET', value=eks_stack.code_bucket)
core.CfnOutput(eks_stack,'ARGO_URL', value='https://'+ cf_nested_stack.argo_cf)
core.CfnOutput(eks_stack,'JUPYTER_URL', value='https://'+ cf_nested_stack.jhub_cf)

app.synth()
