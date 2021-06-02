# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
#!/bin/bash

#!/bin/bash

export stack_name=SparkOnEKS

echo "================================================================================================"
echo "Make sure your CloudFormation stack name $stack_name is correct. "
echo "Change it in the script if you use a different name."
echo "================================================================================================"

# 1. download the project if run the script from AWS CloudShell
if [ $# -eq 0 ]; then
	echo -e "\nDownload github project"
	git clone https://github.com/aws-samples/sql-based-etl-on-amazon-eks.git
fi

# 2. install k8s command tools 
echo -e "\ninstall kubectl tool..."
curl -o kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/1.19.6/2021-01-05/bin/linux/amd64/kubectl
chmod +x kubectl
mkdir -p $HOME/bin && mv kubectl $HOME/bin/kubectl && export PATH=$PATH:$HOME/bin

echo "================================================================================================"
echo " Installing argoCLI tool on Linux ..."
echo " Check out https://github.com/argoproj/argo-workflows/releases for other OS type installation."
echo "================================================================================================"
VERSION=v3.0.2
sudo curl -sLO https://github.com/argoproj/argo/releases/download/${VERSION}/argo-linux-amd64.gz && gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64 && sudo mv ./argo-linux-amd64 /usr/local/bin/argo
argo version --short

# 3. connect to the EKS newly created
echo `aws cloudformation describe-stacks --stack-name SparkOnEKS --query "Stacks[0].Outputs[?starts_with(OutputKey,'eksclusterEKSConfig')].OutputValue" --output text` | bash
echo -e "\ntest EKS connection..."
kubectl get svc

# 4. get Jupyter Hub login
LOGIN_URI=$(aws cloudformation describe-stacks --stack-name $stack_name \
--query "Stacks[0].Outputs[?OutputKey=='JUPYTERURL'].OutputValue" --output text)
JHUB_PWD=$(kubectl -n jupyter get secret jupyter-external-secret -o jsonpath="{.data.password}" | base64 --decode)
echo -e "\n=============================== JupyterHub Login ============================================="
echo -e "Note: Use your own USERNAME, only if it was specified at deployment."
echo -e "\n\nJUPYTER_URL: $LOGIN_URI"
echo "USERNAME: sparkoneks" 
echo "PASSWORD: $JHUB_PWD"
echo "================================================================================================"

