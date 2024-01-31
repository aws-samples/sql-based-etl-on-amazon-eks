# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
#!/bin/bash

#!/bin/bash

export stack_name="${1:-SparkOnEKS}"
export region="${2:-us-east-1}"
echo "================================================================================================="
echo "  Make sure your CloudFormation stack name $stack_name is correct and exists in region: $region  "
echo "  If you use a different name, rerun the script with the parameters:"
echo "      ./deployment/post-deployment.sh <stack_name> <region>"
echo "================================================================================================="

# 1. install k8s command tools 
echo "================================================================================"
echo "  Installing kubectl tool on Linux ..."
echo "  For other operating system, install the kubectl > 1.27 here:"
echo "  https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html"
echo "================================================================================"
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mkdir -p /usr/local/bin && sudo mv kubectl /usr/local/bin/kubectl && export PATH=$PATH:/usr/local/bin/
echo "Installed kubectl version: "
kubectl version --client

echo "================================================================================================"
echo " Installing argoCLI tool on Linux ..."
echo " Check out https://github.com/argoproj/argo-workflows/releases for other OS type installation."
echo "================================================================================================"
VERSION=v3.5.4
sudo curl -sLO https://github.com/argoproj/argo-workflows/releases/download/${VERSION}/argo-linux-amd64.gz && gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64 && sudo mv ./argo-linux-amd64 /usr/local/bin/argo
argo version --short

# 2. connect to the EKS newly created
echo `aws cloudformation describe-stacks --stack-name $stack_name --region $region --query "Stacks[0].Outputs[?starts_with(OutputKey,'eksclusterEKSConfig')].OutputValue" --output text` | bash
echo "Testing EKS connection..."
kubectl get svc

# 3. get Jupyter Hub login
LOGIN_URI=$(aws cloudformation describe-stacks --stack-name $stack_name --region $region \
--query "Stacks[0].Outputs[?OutputKey=='JUPYTERURL'].OutputValue" --output text)
SEC_ID=$(aws secretsmanager list-secrets --region $region --query "SecretList[?not_null(Tags[?Value=='$stack_name'])].Name" --output text)
LOGIN=$(aws secretsmanager get-secret-value --region $region --secret-id $SEC_ID --query SecretString --output text)
echo -e "\n=============================== JupyterHub Login =============================================="
echo -e "\nJUPYTER_URL: $LOGIN_URI"
echo "LOGIN: $LOGIN" 
echo "================================================================================================"