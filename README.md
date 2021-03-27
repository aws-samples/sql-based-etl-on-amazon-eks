# SQL-based ETL with Spark on EKS

We introduce a quality-aware design to increase data processing productivity, by leveraging an open-source [Arc data framework](https://arc.tripl.ai/) for a user-centered declarative ETL solution. We take considerations of the needs and expected skills from customers in data analytics, and accelerate their interaction with ETL practice in order to foster simplicity, while maximizing efficiency.

The sample provides two ways of running the solution shown in the Architecture diagram:
1. Spark on EKS by Argo Workflows tool
2. [EMR on EKS](https://aws.amazon.com/emr/features/eks/) 

![](/spark-on-eks/images/two_architecture.png)

### Test job in Jupyter
![](/spark-on-eks/images/run_jupyter.gif)


### Test Spark Driver self-recovery
![](/spark-on-eks/images/driver_interruption_test.gif)

### Submit Spark job by Argo tool
![](/spark-on-eks/images/submit_job_in_argo.gif)


## Prerequisite
1. Python 3.6 or later. You can find information about downloading and installing Python [here](https://www.python.org/downloads/).
2. AWS CLI version 1.
  Windows: [MSI installer](https://docs.aws.amazon.com/cli/latest/userguide/install-windows.html#install-msi-on-windows)
  Linux, macOS or Unix: [Bundled installer](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html#install-macosos-bundled)
3. [AWS CloudShell](https://console.aws.amazon.com/cloudshell/) is available in your **region**. Otherwise, run all the commands in your local commandline tool.


## Pre-deployment
Assume the AWS CLI on your computer can communicate with services in your deployment account. Otherwise, either set your profile by `export AWS_PROFILE=<your_aws_profile>` , or run the following configuration to setup your AWS account access.

```bash
aws configure
```
* Clone the project

```bash
git clone https://github.com/aws-samples/sql-based-etl-on-amazon-eks.git
cd sql-based-etl-on-amazon-eks
```

## Deploy Infrastructure

The provisining takes about 30 minutes to complete. See the `troubleshooting` section if you have a problem during the deployment. 

The sample provides two options to submit ETL jobs. See the detailed deployment instruction:

1. [Spark on EKS](/spark-on-eks/README.md)
2. [EMR on EKS](/emr-on-eks/README.md)


## Troubleshooting

1. If you see the issue `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)`, most likely it means no default certificate authority for your Python installation on OSX. Refer to the [answer](https://stackoverflow.com/questions/52805115/0nd) installing `Install Certificates.command` should fix your local environment. Otherwise, use [Cloud9](https://aws.amazon.com/cloud9/details/) to deploy the CDK instead.

2. If an error appears during a CDK deployment: `Failed to create resource. IAM role’s policy must include the "ec2:DescribeVpcs" action`. The possible causes are: 1) you have reach the quota limits of Amazon VPC resources per Region in your AWS account. Please deploy to a different region or a different account. 2) based on this [CDK issue](https://github.com/aws/aws-cdk/issues/9027), you can retry without any changes, it will work. 3) If you are in a branch new AWS account, manually delete the AWSServiceRoleForAmazonEKS from IAM role console before the deployment. 


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE.txt) file.