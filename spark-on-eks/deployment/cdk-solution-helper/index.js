/**
 *  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
 *  with the License. A copy of the License is located at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
 *  and limitations under the License.
 */

// Imports
const fs = require('fs');

// Paths
const global_s3_assets = '../global-s3-assets';
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
  });
};
function assetRef(s3BucketRef) {
  // Get the S3 bucket key references from assets file
    const raw_meta = fs.readFileSync(`${global_s3_assets}/SparkOnEKS.assets.json`);
    let template = JSON.parse(raw_meta);
    const metadata = (template.files[s3BucketRef]) ? template.files[s3BucketRef] : {};
    assetPath = metadata.source.path.replace('.json','');
    return assetPath;
};

// For each template in global_s3_assets ...
fs.readdirSync(global_s3_assets).forEach(file => {

  if ( file != 'SparkOnEKS.assets.json') {
    // Import and parse template file
    const raw_template = fs.readFileSync(`${global_s3_assets}/${file}`);
    let template = JSON.parse(raw_template);

    //1. Clean-up parameters section
    setParameter(template);

    const resources = (template.Resources) ? template.Resources : {};
    //2. Clean-up subnet region
    const dummySubnet = Object.keys(resources).filter(function(key) {
      return resources[key].Type === 'AWS::EC2::Subnet'
    });
    dummySubnet.forEach(function(f) {
      const fn = template.Resources[f];
      if (fn.Properties.hasOwnProperty('AvailabilityZone') && fn.Properties.AvailabilityZone.includes('dummy1')) {
        fn.Properties.AvailabilityZone = {'Fn::Sub': '${AWS::Region}'+fn.Properties.AvailabilityZone.replace('dummy1','')};
      };
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
        }};
    });

    //4. Clean-up S3 bucket dependencies
    const replaceS3Bucket = Object.keys(resources).filter(function(key) {
      return (resources[key].Type === "AWS::Lambda::Function" || resources[key].Type === "AWS::Lambda::LayerVersion" || resources[key].Type === "Custom::CDKBucketDeployment" || resources[key].Type === "AWS::CloudFormation::Stack" || resources[key].Type === "AWS::IAM::Policy" || resources[key].Type === "AWS::IAM::Role");
    });
    replaceS3Bucket.forEach(function(f) {
        const fn = template.Resources[f];
        if (fn.Properties.hasOwnProperty('Code') && fn.Properties.Code.hasOwnProperty('S3Bucket')) {
          // Set Lambda::Function S3 bucket reference
          fn.Properties.Code.S3Key = `%%SOLUTION_NAME%%/%%VERSION%%/asset`+fn.Properties.Code.S3Key;
          fn.Properties.Code.S3Bucket = {'Fn::Sub': '%%BUCKET_NAME%%'};
          // Set the handler
          const handler = fn.Properties.Handler;
          fn.Properties.Handler = `${handler}`;
        }
        else if (fn.Properties.hasOwnProperty('Content') && fn.Properties.Content.hasOwnProperty('S3Bucket')) {
          // Set Lambda::LayerVersion S3 bucket reference
          fn.Properties.Content.S3Key = `%%SOLUTION_NAME%%/%%VERSION%%/asset`+fn.Properties.Content.S3Key;
          fn.Properties.Content.S3Bucket = {'Fn::Sub': '%%BUCKET_NAME%%'};    
        }
        else if (fn.Properties.hasOwnProperty('SourceBucketNames')) {
          // Set CDKBucketDeployment S3 bucket reference
          fn.Properties.SourceObjectKeys = [`%%SOLUTION_NAME%%/%%VERSION%%/asset`+fn.Properties.SourceObjectKeys[0]];
          fn.Properties.SourceBucketNames = [{'Fn::Sub': '%%BUCKET_NAME%%'}];
        }
        else if (fn.Properties.hasOwnProperty('PolicyName') && fn.Properties.PolicyName.includes('CustomCDKBucketDeployment')) {
          // Set CDKBucketDeployment S3 bucket Policy reference
          fn.Properties.PolicyDocument.Statement.forEach(function(sub,i) {
            sub.Resource.forEach(function(resource){
              arrayKey = Object.keys(resource);
              if (typeof(resource[arrayKey][1]) === 'object') {
                resource[arrayKey][1].filter(function(key){
                    if (key.hasOwnProperty('Ref')) {
                      fn.Properties.PolicyDocument.Statement[i].Resource = [
                      {"Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},":s3:::%%BUCKET_NAME%%"]]},
                      {"Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},":s3:::%%BUCKET_NAME%%/*"]]}
                      ]
                    };
                  });
                };
              });
            });
        }
        else if (fn.Properties.hasOwnProperty('TemplateURL')) {
          // Set NestedStack S3 bucket reference
          key=fn.Properties.TemplateURL['Fn::Join'][1][2].split('/')[2].replace('.json','');
          assetPath = assetRef(key);
          fn.Properties.TemplateURL = {
            'Fn::Join': [
              '',
              [
                  'https://s3.',
                  {
                      'Ref' : 'AWS::URLSuffix'
                  },
                  '/',
                  `%%TEMPLATE_OUTPUT_BUCKET%%/%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`
              ]
          ]
          };
        }
        //5. Clean-up Account ID and region from EKS IAM roles
        else if (fn.Metadata['aws:cdk:path'].includes('EKS/Resource/CreationRole') && fn.Properties.hasOwnProperty('PolicyDocument')){
          // reset EKS creation policy
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
                };
            });
        }
        // reset EKS roles
        else if (fn.Properties.hasOwnProperty('AssumeRolePolicyDocument')){
          if (fn.Metadata['aws:cdk:path'].includes('SparkOnEKS/iam_roles/clusterAdmin') || fn.Metadata['aws:cdk:path'].includes('EKS/Resource/CreationRole')){
            fn.Properties.AssumeRolePolicyDocument.Statement.forEach(function(sub,i){
              if (sub.Principal.hasOwnProperty('AWS') && typeof(sub.Principal.AWS['Fn::Join']) === 'object'){
                fn.Properties.AssumeRolePolicyDocument.Statement[i].Principal.AWS={
                 "Fn::Join": ["",["arn:",{"Ref": "AWS::Partition"},":iam::",{"Ref": "AWS::AccountId"},":root"]]
                }}
            });
          };
        };  
    });
    
    //6. Output modified template file
    const output_template = JSON.stringify(template, null, 2);
    fs.writeFileSync(`${global_s3_assets}/${file}`, output_template);
  }; 
});