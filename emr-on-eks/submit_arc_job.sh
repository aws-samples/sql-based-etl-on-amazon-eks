#!/bin/bash

# SPDX-FileCopyrightText: Copyright 2021 Amazon.com, Inc. or its affiliates.
# SPDX-License-Identifier: MIT-0

# Define params
export AWS_DEFAULT_REGION=us-east-1
export EKSCLUSTERNAME=eks-cluster
export EMRCLUSTERNAME=emr-on-$EKSCLUSTERNAME
export ROLENAME=${EMRCLUSTERNAME}-execution-role

#submit test job
export EMRCLUSTERID=$(aws emr-containers list-virtual-clusters --query "virtualClusters[?name == '${EMRCLUSTERNAME}' && state == 'RUNNING'].id" --output text)
export ACCOUNTID=$(aws sts get-caller-identity --query Account --output text)
export ROLEARN=arn:aws:iam::$ACCOUNTID:role/$ROLENAME
export OUTPUTS3BUCKET=${EMRCLUSTERNAME}-${ACCOUNTID}

# update aws CLI to the latest version (we will require aws cli version >= 2.1.14)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" 
unzip -q -o /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install --update

# install kubectl
curl -L "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl" \
    -o "/tmp/kubectl" 
chmod +x /tmp/kubectl
sudo mv /tmp/kubectl /usr/local/bin

# sumbit job

aws emr-containers start-job-run --virtual-cluster-id $EMRCLUSTERID \
    --name arc-job --execution-role-arn $ROLEARN --release-label emr-6.2.0-latest \
    --job-driver '{"sparkSubmitJobDriver": {"entryPoint": "https://repo1.maven.org/maven2/ai/tripl/arc_2.12/3.6.2/arc_2.12-3.6.2.jar", "entryPointArguments":["--etl.config.uri=https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/emr-on-eks/green_taxi_load.ipynb"], "sparkSubmitParameters": "--packages com.typesafe:config:1.4.0 --class ai.tripl.arc.ARC --conf spark.executor.instances=10 --conf spark.executor.memory=4G --conf spark.driver.memory=2G --conf spark.executor.cores=2 --conf spark.kubernetes.driverEnv.ETL_CONF_ENV=production --conf spark.kubernetes.driverEnv.OUTPUT=s3://'$OUTPUTS3BUCKET'/output/ --conf spark.kubernetes.driverEnv.SCHEMA=https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/emr-on-eks/green_taxi_schema.json"}}' \
    --configuration-overrides '{"monitoringConfiguration": {"cloudWatchMonitoringConfiguration": {"logGroupName": "/aws/eks/'$EKSCLUSTERNAME'/jobs", "logStreamNamePrefix": "arc-job"}}}'

echo "Job submitted"
echo "Navigate to https://console.aws.amazon.com/emr/home?#/eks/clusters/"${EMRCLUSTERID}" to view job status"

echo "Navigate to the output S3 bucket here https://s3.console.aws.amazon.com/s3/buckets/"${OUTPUTS3BUCKET}" to view outputs"
