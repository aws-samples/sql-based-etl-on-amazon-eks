#!/bin/bash
export stack_name=SparkOnEKS

echo "Delete application code asset S3 Bucket"
code_bucket=$(aws cloudformation describe-stacks --stack-name $stack_name \
	--query "Stacks[0].Outputs[?OutputKey=='CODEBUCKET'].OutputValue" \
	--output text)
aws s3 rm s3://$code_bucket --recursive
aws s3 rb s3://$code_bucket --force


echo "Delete Arc docker image from ECR"
repo_uri=$(aws cloudformation describe-stacks --stack-name $stack_name \
	--query "Stacks[0].Outputs[?OutputKey=='IMAGEURI'].OutputValue" \
	--output text)
cfn_repo_name=$(echo $repo_uri| cut -d'/' -f 2 | cut -d ':' -f 1)  
repo=$(aws ecr describe-repositories --repository-names $cfn_repo_name --query 'repositories[].repositoryName' --output text)
if ! [ -z "$repo" ] 
then
	aws ecr delete-repository --repository-name $cfn_repo_name --force
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
# delete ALB
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

echo "Delete the rest of resources via CloudFormation, ensure the stack name is $stack_name"
# cd source; cdk destroy
# aws cloudformation delete-stack --stack-name <your_stack_name>
aws cloudformation delete-stack --stack-name $stack_name