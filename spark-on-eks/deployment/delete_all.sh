# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
#!/bin/bash

export stack_name="${1:-SparkOnEKS}"
lower_stack_name=$(echo $stack_name | tr '[:upper:]' '[:lower:]')

code_bucket="s3://"$(aws s3api list-buckets --query 'Buckets[?starts_with(Name,`'${lower_stack_name:0:18}'`)==`true`]'.Name --output text)
if ! [ -z "$code_bucket" ] 
then	
	echo "Delete vpc log from asset S3 Bucket"
	aws s3 rm ${code_bucket}/vpcRejectlog/
fi

echo "Drop a Delta Lake table default.contact_snapshot"
accountId=$(aws sts get-caller-identity --query Account --output text)
tbl1=$(aws glue get-tables --database-name 'default' --query 'TableList[?starts_with(Name,`contact_snapshot`)==`true`]'.Name --output text)
tbl2=$(aws glue get-tables --database-name 'default' --query 'TableList[?starts_with(Name,`contact_snapshot_jhub`)==`true`]'.Name --output text)
if ! [ -z "$tbl1" ]
then
	aws athena start-query-execution --query-string "DROP TABLE default.contact_snapshot" --result-configuration OutputLocation=s3://aws-athena-query-results-$accountId
fi
if ! [ -z "$tbl2" ] 
then
	aws athena start-query-execution --query-string "DROP TABLE default.deltalake_contact_jhub" --result-configuration OutputLocation=s3://aws-athena-query-results-$accountId
fi

echo "Delete ALB"
argoALB=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[?starts_with(DNSName,`k8s-argo`)==`true`].LoadBalancerArn' --output text)
jhubALB=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[?starts_with(DNSName,`k8s-jupyter`)==`true`].LoadBalancerArn' --output text)

if ! [ -z "$argoALB" ]
then
	aws elbv2 delete-load-balancer --load-balancer-arn $argoALB
	sleep 5
fi	
if ! [ -z "$jhubALB" ]
then
	aws elbv2 delete-load-balancer --load-balancer-arn $jhubALB
	sleep 5
fi

echo "Delete Target groups"
argoTG=$(aws elbv2 describe-target-groups --query 'TargetGroups[?starts_with(TargetGroupName,`k8s-argo`)==`true`].TargetGroupArn' --output text)
jhubTG=$(aws elbv2 describe-target-groups --query 'TargetGroups[?starts_with(TargetGroupName,`k8s-jupyter`)==`true`].TargetGroupArn' --output text)

if ! [ -z "$argoTG" ]
then
	aws elbv2 delete-target-group --target-group-arn $argoTG 
fi	
if ! [ -z "$jhubTG" ]
then
	aws elbv2 delete-target-group --target-group-arn $jhubTG 
fi	

echo "Delete the rest of resources via CloudFormation, ensure the stack name $stack_name is correct"
# cd source; cdk destroy
# aws cloudformation delete-stack --stack-name <your_stack_name>
aws cloudformation delete-stack --stack-name $stack_name