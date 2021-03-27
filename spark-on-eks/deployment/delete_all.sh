# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

#!/bin/bash

echo "Drop a Delta Lake table default.contact_snapshot"
accountId=$(aws sts get-caller-identity --query Account --output text)
aws athena start-query-execution --query-string "DROP TABLE default.contact_snapshot" --result-configuration OutputLocation=s3://aws-athena-query-results-$accountId
aws athena start-query-execution --query-string "DROP TABLE default.contact_snapshot_jhub" --result-configuration OutputLocation=s3://aws-athena-query-results-$accountId


echo "Delete ALB"
# delete ALB
argoALB=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[?starts_with(DNSName,`k8s-argo`)==`true`].LoadBalancerArn' --output text)
jhubALB=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[?starts_with(DNSName,`k8s-jupyter`)==`true`].LoadBalancerArn' --output text)

aws elbv2 delete-load-balancer --load-balancer-arn $argoALB
aws elbv2 delete-load-balancer --load-balancer-arn $jhubALB
sleep 15

echo "Delete Target groups"
argoTG=$(aws elbv2 describe-target-groups --query 'TargetGroups[?starts_with(TargetGroupName,`k8s-argo`)==`true`].TargetGroupArn' --output text)
jhubTG=$(aws elbv2 describe-target-groups --query 'TargetGroups[?starts_with(TargetGroupName,`k8s-jupyter`)==`true`].TargetGroupArn' --output text)

aws elbv2 delete-target-group --target-group-arn $argoTG 
aws elbv2 delete-target-group --target-group-arn $jhubTG 


echo "Delete the rest of resources by CDK CLI or CloudFormation, ensure the stack name is correct"
# cd source
# cdk destroy
aws cloudformation delete-stack --stack-name SparkOnEKS


