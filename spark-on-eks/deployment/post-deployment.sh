# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
#!/bin/bash

#!/bin/bash

export stack_name=SparkOnEKS

echo "================================================================================================"
echo "Make sure your CloudFormation stack name $stack_name is correct. "
echo "Change it in the script if you use a different name."
echo "================================================================================================"

# 0. download the project if run the script from AWS CloudShell
if [ -n "$1" ]; then
	git clone https://github.com/aws-samples/sql-based-etl-on-amazon-eks.git
	cd sql-based-etl-on-amazon-eks
fi

# 1. update ECR endpoint in example jobs
export ECR_IMAGE_URI=$(aws cloudformation describe-stacks --stack-name $stack_name \
--query "Stacks[0].Outputs[?OutputKey=='IMAGEURI'].OutputValue" --output text)
echo "Update ECR url in sample job files"
sed -i.bak "s|{{ECR_URL}}|${ECR_IMAGE_URI}|g" source/example/*.yaml

find . -type f -name "*.bak" -delete

# 2. install k8s command tools 
curl -o kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/1.19.6/2021-01-05/bin/linux/amd64/kubectl
chmod +x kubectl
mkdir -p $HOME/bin && mv kubectl $HOME/bin/kubectl && export PATH=$PATH:$HOME/bin

VERSION=v2.12.9
sudo curl -sLO https://github.com/argoproj/argo/releases/download/${VERSION}/argo-linux-amd64.gz && gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64 && sudo mv ./argo-linux-amd64 /usr/local/bin/argo
argo version --short

# 3. connect to the EKS newly created
echo `aws cloudformation describe-stacks --stack-name SparkOnEKS --query "Stacks[0].Outputs[?starts_with(OutputKey,'eksclusterEKSConfig')].OutputValue" --output text` | bash
# test the connection
kubectl get svc

# 4. get Jupyter Hub login
LOGIN_URI=$(aws cloudformation describe-stacks --stack-name $stack_name \
--query "Stacks[0].Outputs[?OutputKey=='JUPYTERURL'].OutputValue" --output text)
JHUB_PWD=$(kubectl -n jupyter get secret jupyter-external-secret -o jsonpath="{.data.password}" | base64 --decode)

echo "Note: Use default login username, otherwise use your own if it has been specified at the deployment."
echo -e"\n\nJUPYTER_URL: $LOGIN_URI"
echo -e "\nUSERNAME: sparkoneks" 
echo -e "\nPASSWORD: $JHUB_PWD"
