# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from aws_cdk import (RemovalPolicy, aws_s3 as s3, aws_s3_deployment as s3deploy)
from constructs import Construct
import os

class S3AppCodeConst(Construct):

    @property
    def code_bucket(self):
        return self._code_bucket

    def __init__(self,scope: Construct, id: str, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

       # Upload application code to S3 bucket 
        artifact_bucket=s3.Bucket(self, id, 
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.KMS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            access_control = s3.BucketAccessControl.LOG_DELIVERY_WRITE
        )

        source_dir=os.path.split(os.environ['VIRTUAL_ENV'])[0]
        s3deploy.BucketDeployment(self, "DeployCode",
            sources=[s3deploy.Source.asset(source_dir+'/deployment/app_code')],
            destination_bucket= artifact_bucket,
            destination_key_prefix="app_code"
        )
        self._code_bucket = artifact_bucket.bucket_name
