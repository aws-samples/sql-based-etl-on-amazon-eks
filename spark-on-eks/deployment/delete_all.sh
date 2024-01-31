# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
#!/bin/bash

export stack_name="${1:-SparkOnEKS}"
export region="${2:-us-east-1}"

echo "================================================================================================="
echo "  Make sure your CloudFormation stack name $stack_name is correct and exists in region: $region  "
echo "  If you use a different name, rerun the script with the parameters:"
echo "      ./deployment/delete_all.sh <stack_name> <region>"
echo "================================================================================================="

code_bucket=$(aws cloudformation describe-stacks --stack-name $stack_name --region $region --query "Stacks[0].Outputs[?OutputKey=='CODEBUCKET'].OutputValue" --output text)
if ! [ -z "$code_bucket" ] 
then	
	if ! [ -z $(aws s3api list-buckets --region $region --query 'Buckets[?Name==`'$code_bucket'`].Name' --output text) ]; then
		echo "Delete logs from S3"
		aws s3 rm s3://${code_bucket}/vpcRejectlog/
		echo "Delete athena query result from S3"
		aws s3 rm s3://${code_bucket}/athena-query-result/
	fi	
fi

# delete glue tables
tbl1=$(aws glue get-tables --region $region --database-name 'default' --query 'TableList[?starts_with(Name,`contact_snapshot`)==`true`]'.Name --output text)
tbl2=$(aws glue get-tables --region $region --database-name 'default' --query 'TableList[?starts_with(Name,`deltalake_contact_jhub`)==`true`]'.Name --output text)
if ! [ -z "$tbl1" ] 
then
	echo "Drop a Delta Lake table default.contact_snapshot"
	aws athena start-query-execution --region $region --query-string "DROP TABLE default.contact_snapshot" --result-configuration OutputLocation=s3://$code_bucket/athena-query-result
fi
if ! [ -z "$tbl2" ] 
then
	echo "Drop a Delta Lake table default.deltalake_contact_jhub"
	aws athena start-query-execution --region $region --query-string "DROP TABLE default.deltalake_contact_jhub" --result-configuration OutputLocation=s3://$code_bucket/athena-query-result
fi

argoALB=$(aws elbv2 describe-load-balancers --region $region --query 'LoadBalancers[?starts_with(DNSName,`k8s-argo`)==`true`].LoadBalancerArn' --output text)
jhubALB=$(aws elbv2 describe-load-balancers --region $region --query 'LoadBalancers[?starts_with(DNSName,`k8s-jupyter`)==`true`].LoadBalancerArn' --output text)
if ! [ -z "$argoALB" ]
then
	echo "Delete Argo ALB"
	aws elbv2 delete-load-balancer --load-balancer-arn $argoALB --region $region
	sleep 5
fi	
if ! [ -z "$jhubALB" ]
then
	echo "Delete Jupyter ALB"
	aws elbv2 delete-load-balancer --load-balancer-arn $jhubALB --region $region
	sleep 5
fi

argoTG=$(aws elbv2 describe-target-groups --region $region --query 'TargetGroups[?starts_with(TargetGroupName,`k8s-argo`)==`true`].TargetGroupArn' --output text)
jhubTG=$(aws elbv2 describe-target-groups --region $region --query 'TargetGroups[?starts_with(TargetGroupName,`k8s-jupyter`)==`true`].TargetGroupArn' --output text)
if ! [ -z "$argoTG" ]
then
	sleep 5
	echo "Delete Argo Target groups"
	aws elbv2 delete-target-group --target-group-arn $argoTG --region $region
fi	
if ! [ -z "$jhubTG" ]
then
	sleep 5
	echo "Delete Jupyter Target groups"
	aws elbv2 delete-target-group --target-group-arn $jhubTG --region $region
fi	

# delete the rest from CF
echo "Delete the rest of resources by CloudFormation delete command"
aws cloudformation delete-stack --stack-name $stack_name --region $region