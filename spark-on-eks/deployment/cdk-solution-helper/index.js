#!/usr/bin/env node
/**********************************************************************************************************************
 *  Copyright 2020-2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                      *
 *                                                                                                                    *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance    *
 *  with the License. A copy of the License is located at                                                             *
 *                                                                                                                    *
 *      http://www.apache.org/licenses/LICENSE-2.0                                                                    *
 *                                                                                                                    *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES *
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    *
 *  and limitations under the License.                                                                                *
 *********************************************************************************************************************/

// Imports
const fs = require('fs');

// Paths
var currentPath = process.cwd();
const global_s3_assets = currentPath+'/../deployment/global-s3-assets';
const solution_name='SparkOnEKS';

function setParameter(template) {
    const parameters = (template.Parameters) ? template.Parameters : {};
    const assetParameters = Object.keys(parameters).filter(function(key) {
      return key.includes('BootstrapVersion');
    });
    assetParameters.forEach(function(a) {
        template.Parameters[a] = undefined;
    });
    const rules = (template.Rules) ? template.Rules : {};
    const rule = Object.keys(rules).filter(function(key) {
      return key.includes('CheckBootstrapVersion');
    });
    rule.forEach(function(a) {
      template.Rules[a] = undefined;
  })
}
function setOutput(template) {
  const outputs = (template.Outputs) ? template.Outputs : {};
  const output=Object.keys(outputs).filter(function(key){
    if(typeof(outputs[key].Value["Fn::Join"]) === 'object' && typeof(outputs[key].Value["Fn::Join"][1][0]) === 'string'){
      return(outputs[key].Value["Fn::Join"][1][0].startsWith('aws eks'))
    }
  })
  output.forEach(i => 
    template.Outputs[i].Value={
      "Fn::Join": ["",[outputs[i].Value["Fn::Join"][1][0],outputs[i].Value["Fn::Join"][1][1],
      " --region ",{"Ref": "AWS::Region"}," --role-arn ",outputs[i].Value["Fn::Join"][1][3]]]
    })
}

function assetRef(s3BucketRef) {
  // Get S3 bucket key references from assets file
    const raw_meta = fs.readFileSync(`${global_s3_assets}/${solution_name}.assets.json`);
    let template = JSON.parse(raw_meta);
    const metadata = (template.files[s3BucketRef]) ? template.files[s3BucketRef] : {};
    var assetPath = metadata.source.path.replace('.json','');
    return assetPath;
}

// For each template in global_s3_assets ...
fs.readdirSync(global_s3_assets).forEach(file => {
  if ( file != `${solution_name}.assets.json`) {
    // Import and parse template file
    const raw_template = fs.readFileSync(`${global_s3_assets}/${file}`);
    let template = JSON.parse(raw_template);

    //1. Clean-up parameters section
    setParameter(template);
    setOutput(template);

    const resources = (template.Resources) ? template.Resources : {};
    //2. Clean-up subnet region
    const dummySubnet = Object.keys(resources).filter(function(key) {
      return resources[key].Type === 'AWS::EC2::Subnet'
    });
    dummySubnet.forEach(function(f) {
      const fn = template.Resources[f];
      if (fn.Properties.hasOwnProperty('AvailabilityZone') && fn.Properties.AvailabilityZone.includes('dummy1')) {
        fn.Properties.AvailabilityZone = {'Fn::Sub': '${AWS::Region}'+fn.Properties.AvailabilityZone.replace('dummy1','')};
      }
    });

    //3. Clean-up VPC endpoint region
    const vpcEP= Object.keys(resources).filter(function(key) {
      return resources[key].Type === 'AWS::EC2::VPCEndpoint'
    });
    vpcEP.forEach(function(f) {
      const fn = template.Resources[f];
      if (fn.Properties.hasOwnProperty('ServiceName') && typeof(fn.Properties.ServiceName) === 'string') {
          fn.Properties.ServiceName = {
            "Fn::Join": ["",["com.amazonaws.",{"Ref": "AWS::Region"},".",
                fn.Properties.ServiceName.split('.').slice(3).join('.')
            ]]
        }}
    });

    //4. Clean-up Account ID and region to enable cross account deployment
    const rsrctype=["AWS::Lambda::Function","AWS::Lambda::LayerVersion","Custom::CDKBucketDeployment", "AWS::CloudFormation::Stack","AWS::IAM::Policy","AWS::IAM::Role","AWS::KMS::Key","Custom::AWSCDK-EKS-HelmChart","Custom::AWSCDK-EKS-KubernetesResource"] 
    const focusTemplate = Object.keys(resources).filter(function(key) {
      return (resources[key].Type.indexOf(rsrctype) < 0)
    });
    focusTemplate.forEach(function(f) {
        const fn = template.Resources[f];
        if (fn.Properties.hasOwnProperty('Code') && fn.Properties.Code.hasOwnProperty('S3Bucket')) {
          // Set Lambda::Function S3 bucket reference
          fn.Properties.Code.S3Key = `%%SOLUTION_NAME%%/%%VERSION%%/asset`+fn.Properties.Code.S3Key;
          fn.Properties.Code.S3Bucket = {'Fn::Sub': '%%BUCKET_NAME%%-${AWS::Region}'};
          // Set the handler
          const handler = fn.Properties.Handler;
          fn.Properties.Handler = `${handler}`;
        }
        else if (fn.Properties.hasOwnProperty('Content') && fn.Properties.Content.hasOwnProperty('S3Bucket')) {
          // Set Lambda::LayerVersion S3 bucket reference
          fn.Properties.Content.S3Key = `%%SOLUTION_NAME%%/%%VERSION%%/asset`+fn.Properties.Content.S3Key;
          fn.Properties.Content.S3Bucket = {'Fn::Sub': '%%BUCKET_NAME%%-${AWS::Region}'};    
        }
        else if (fn.Properties.hasOwnProperty('SourceBucketNames')) {
          // Set CDKBucketDeployment S3 bucket reference
          fn.Properties.SourceObjectKeys = [`%%SOLUTION_NAME%%/%%VERSION%%/asset`+fn.Properties.SourceObjectKeys[0]];
          fn.Properties.SourceBucketNames = [{'Fn::Sub': '%%BUCKET_NAME%%-${AWS::Region}'}];
        }
        else if (fn.Properties.hasOwnProperty('PolicyName') && fn.Properties.PolicyName.includes('CustomCDKBucketDeployment')) {
          // Set CDKBucketDeployment S3 bucket Policy reference
          fn.Properties.PolicyDocument.Statement.forEach(function(sub,i) {
            if (typeof(sub.Resource[i]) === 'object') {
              sub.Resource.forEach(function(resource){
                var arrayKey = Object.keys(resource);
                if (typeof(resource[arrayKey][1]) === 'object') {
                  resource[arrayKey][1].filter(function(s){
                      if (s.hasOwnProperty('Ref')) {
                        fn.Properties.PolicyDocument.Statement[i].Resource = [
                        {"Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},":s3:::%%BUCKET_NAME%%-",{"Ref": "AWS::Region"}]]},
                        {"Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},":s3:::%%BUCKET_NAME%%-",{"Ref": "AWS::Region"},"/*"]]}
                        ]
                      }
                    });
                  }
                })
            }
            });
        }
        // Set NestedStack S3 bucket reference
        else if (fn.Properties.hasOwnProperty('TemplateURL')) {
          var key=fn.Properties.TemplateURL['Fn::Join'][1][2].split('/')[2].replace('.json','');
          var assetPath = assetRef(key);
          fn.Properties.TemplateURL = {
            'Fn::Join': ['',['https://s3.',{'Ref' : 'AWS::URLSuffix'},'/',`%%TEMPLATE_OUTPUT_BUCKET%%/%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`]]
          };
        }
        // reset EKS creation policy
        else if (fn.Metadata['aws:cdk:path'].includes('EKS/Resource/CreationRole') && fn.Properties.hasOwnProperty('PolicyDocument')){
          fn.Properties.PolicyDocument.Statement.forEach(function(sub,i) {
            if (typeof(sub.Resource['Fn::Join']) === 'object') {
              fn.Properties.PolicyDocument.Statement[i].Resource={
                "Fn::Join": ["",[
                    "arn:",{"Ref": "AWS::Partition"},
                    ":eks:",{"Ref": "AWS::Region"},":",{"Ref": "AWS::AccountId"},
                    ":",sub.Resource['Fn::Join'][1][2].split(':').pop()]]
              };
            }
            else if (typeof(sub.Resource[0]) === 'object') {
              fn.Properties.PolicyDocument.Statement[i].Resource=[
                {
                  "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},
                  ":eks:",{"Ref": "AWS::Region"},":",{"Ref": "AWS::AccountId"},
                    ":",sub.Resource[0]['Fn::Join'][1][2].split(':').pop()]]
                },
                {
                "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},
                ":eks:",{"Ref": "AWS::Region"},":",{"Ref": "AWS::AccountId"},
                  ":",sub.Resource[1]['Fn::Join'][1][2].split(':').pop()]] 
                }] 
              }
            });
        }
        // reset IAM assume roles
        else if (fn.Properties.hasOwnProperty('AssumeRolePolicyDocument')){
          const metadata=["iam_roles/clusterAdmin","EKS/Resource/CreationRole","S3Trigger/CodePipelineActionRole","DockerImageBuild/CodePipelineActionRole","waiter-state-machine/Role"]
          metadata.forEach(function (i){
            if (fn.Metadata['aws:cdk:path'].includes(i)){
              fn.Properties.AssumeRolePolicyDocument.Statement.forEach(function(sub,i){
                if (sub.Principal.hasOwnProperty('AWS') && typeof(sub.Principal.AWS['Fn::Join']) === 'object'){
                  fn.Properties.AssumeRolePolicyDocument.Statement[i].Principal.AWS={
                   "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},":iam::",{"Ref": "AWS::AccountId"},":root"]]
                  }}
                else {
                  fn.Properties.AssumeRolePolicyDocument.Statement[i].Principal.Service={
                    "Fn::Join": ["",["states.",{"Ref": "AWS::Region"},".amazonaws.com"]]
                }}  
              });
            }
          })
        }
        // Set KMS key policy pincipal   
        else if (fn.Properties.hasOwnProperty('KeyPolicy')) { 
          fn.Properties.KeyPolicy.Statement.forEach(function(sub,i){
            if (sub.Principal.hasOwnProperty('AWS') && typeof(sub.Principal.AWS['Fn::Join']) === 'object'){
                fn.Properties.KeyPolicy.Statement[i].Principal.AWS={
                  "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},":iam::",{"Ref": "AWS::AccountId"},":root"]]
            }}
            if (sub.hasOwnProperty('Condition') && typeof(sub.Condition.StringEquals['kms:ViaService']) === 'string'){
                fn.Properties.KeyPolicy.Statement[i].Condition.StringEquals['kms:ViaService']={
                  "Fn::Join": ["",["secretsmanager.",{"Ref": "AWS::Region"},".amazonaws.com"]]
            }}
          });
        }
        // Set codebuild defualt policy
        else if (fn.Properties.hasOwnProperty('PolicyName') && fn.Properties.PolicyName.includes('imageDockerBuildRoleDefaultPolicy')){      
          fn.Properties.PolicyDocument.Statement.forEach(function(sub,i) {
            if (typeof(sub.Resource['Fn::Join']) === 'object') {
              fn.Properties.PolicyDocument.Statement[i].Resource={
                "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},
                ":codebuild:",{"Ref": "AWS::Region"},":",{"Ref": "AWS::AccountId"},":report-group/",
                sub.Resource['Fn::Join'][1][3],"-*"
              ]]};

            }
            else if (typeof(sub.Resource[0]) === 'object') {
              sub.Resource.forEach(function(resource){
                if (typeof(resource['Fn::Join']) === 'object' && resource['Fn::Join'][1][1].hasOwnProperty('Ref')){
                  fn.Properties.PolicyDocument.Statement[i].Resource=[{
                    "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},
                    ":logs:",{"Ref": "AWS::Region"},":",{"Ref": "AWS::AccountId"},":log-group:/aws/codebuild/",
                    resource['Fn::Join'][1][3]]]
                  },
                  {
                    "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},
                    ":logs:",{"Ref": "AWS::Region"},":",{"Ref": "AWS::AccountId"},":log-group:/aws/codebuild/",
                    resource['Fn::Join'][1][3],":*"]]
                  }]
                }})}
            })
          }
          // Set CloudFront logging bucket
          else if (fn.Properties.hasOwnProperty('DistributionConfig')){
            fn.Properties.DistributionConfig.Logging.Bucket= {
              "Fn::Join": ["",[fn.Properties.DistributionConfig.Logging.Bucket['Fn::Join'][1][0],
              ".s3.",{"Ref": "AWS::Region"},".",{"Ref": "AWS::URLSuffix"}]]
            }
          }
          // Set region in JupyterHub
          else if (fn.Properties.Release ==='jhub'){
            var array = fn.Properties.Values["Fn::Join"][1];
            var region_array = array[2].split("ETL_CONF_AWS_REGION")[1].split(",");
            region_array.shift();
            fn.Properties.Values = {"Fn::Join": ["",[
              array[0],array[1],
              "\",\"ETL_CONF_AWS_REGION\":\"",{"Ref": "AWS::Region"},"\"},",region_array.toString()]]
            }
          }
          else if (fn.Metadata['aws:cdk:path'].includes('JHubConfig/Resource')){
            var array = fn.Properties.Manifest["Fn::Join"][1];
            var region_array=array[4].split("region")[1].split(",");
            region_array.shift();
            fn.Properties.Manifest = {"Fn::Join": ["",[
              array[0],array[1],array[2],array[3],
              array[4].split("region")[0],"region\":\"",{"Ref": "AWS::Region"},"\",",region_array.toString(),array[5],array[6]]]
            }
          }
    });
    
    //6. Output modified template file
    const output_template = JSON.stringify(template, null, 2);
    fs.writeFileSync(`${global_s3_assets}/${file}`, output_template);
  }
});