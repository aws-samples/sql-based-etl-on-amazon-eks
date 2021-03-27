# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
#!/bin/bash

# install k8s command tool kubectl 
curl -o kubectl "https://amazon-eks.s3.us-west-2.amazonaws.com/1.18.9/2020-11-02/bin/linux/amd64/kubectl"
chmod +x kubectl
mkdir -p $HOME/bin && mv kubectl $HOME/bin/kubectl && export PATH=$PATH:$HOME/bin

# install Argo CLI tool
VERSION=v2.12.9
sudo curl -sLO https://github.com/argoproj/argo/releases/download/${VERSION}/argo-linux-amd64.gz && gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64 && sudo mv ./argo-linux-amd64 /usr/local/bin/argo
argo version --short