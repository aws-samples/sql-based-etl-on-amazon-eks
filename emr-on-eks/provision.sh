#!/bin/bash

# SPDX-FileCopyrightText: Copyright 2021 Amazon.com, Inc. or its affiliates.
# SPDX-License-Identifier: MIT-0

# Define params
export AWS_DEFAULT_REGION=us-east-1
export EKSCLUSTERNAME=eks-cluster
export EMRCLUSTERNAME=emr-on-$EKSCLUSTERNAME
export ROLENAME=${EMRCLUSTERNAME}-execution-role

# Using EKS Fargate mode, uncomment to use EKS EC2 mode
EKSCTL_PARAM="--fargate"
# EKSCTL_PARAM="--nodes 6 --node-type t3.xlarge"

# install eksctl (https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/setting-up-eksctl.html)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# update aws CLI to the latest version (we will require aws cli version >= 2.1.14)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" 
unzip -q -o /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install --update

# install kubectl 
curl -L "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl" \
    -o "/tmp/kubectl" 
chmod +x /tmp/kubectl
sudo mv /tmp/kubectl /usr/local/bin

# Provision eks cluster called “eks-fargate” backed by fargate
eksctl create cluster --name $EKSCLUSTERNAME --with-oidc --zones ${AWS_DEFAULT_REGION}a,${AWS_DEFAULT_REGION}b $EKSCTL_PARAM
aws eks update-kubeconfig --name $EKSCLUSTERNAME

# Create kubernetes namespace 'emr' for EMR
kubectl create namespace emr

# Create fargate profile 'fp-emr' for namespace 'emr'
eksctl create fargateprofile --cluster $EKSCLUSTERNAME --name fp-emr --namespace emr

# Wait for EKS cluster to finish provisioning, enable all logging
# Enable cluster access for Amazon EMR on EKS (https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/setting-up-cluster-access.html) in the 'emr' kubernetes namespace by running:
eksctl create iamidentitymapping --cluster $EKSCLUSTERNAME --namespace "emr" --service-name "emr-containers"
eksctl utils update-cluster-logging --cluster $EKSCLUSTERNAME --enable-types all --approve

# create S3 bucket for output
export ACCOUNTID=$(aws sts get-caller-identity --query Account --output text)
export OUTPUTS3BUCKET=${EMRCLUSTERNAME}-${ACCOUNTID}
aws s3api create-bucket --bucket $OUTPUTS3BUCKET

# Create a job execution role (https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/creating-job-execution-role.html)
cat > /tmp/job-execution-policy.json <<EOL
{
    "Version": "2012-10-17",
    "Statement": [ 
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": ["arn:aws:s3:::${OUTPUTS3BUCKET}","arn:aws:s3:::${OUTPUTS3BUCKET}/*", "arn:aws:s3:::nyc-tlc","arn:aws:s3:::nyc-tlc/*"]
        }, 
        {
            "Effect": "Allow",
            "Action": [ "logs:PutLogEvents", "logs:CreateLogStream", "logs:DescribeLogGroups", "logs:DescribeLogStreams", "logs:CreateLogGroup" ],
            "Resource": [ "arn:aws:logs:*:*:*" ]
        }
    ]
}

EOL

cat > /tmp/trust-policy.json <<EOL
{
  "Version": "2012-10-17",
  "Statement": [ {
      "Effect": "Allow",
      "Principal": { "Service": "eks.amazonaws.com" },
      "Action": "sts:AssumeRole"
    } ]
}

EOL

ACCOUNTID=$(aws sts get-caller-identity --query Account --output text)
aws iam create-policy --policy-name $ROLENAME-policy --policy-document file:///tmp/job-execution-policy.json
aws iam create-role --role-name $ROLENAME --assume-role-policy-document file:///tmp/trust-policy.json
aws iam attach-role-policy --role-name $ROLENAME --policy-arn arn:aws:iam::$ACCOUNTID:policy/$ROLENAME-policy
aws emr-containers update-role-trust-policy --cluster-name $EKSCLUSTERNAME --namespace emr --role-name $ROLENAME

# Create emr virtual cluster
aws emr-containers create-virtual-cluster --name $EMRCLUSTERNAME \
    --container-provider '{
        "id": "'$EKSCLUSTERNAME'",
        "type": "EKS",
        "info": { "eksInfo": { "namespace": "emr" } }
    }'

echo "Finished, proceed to submitting a job"