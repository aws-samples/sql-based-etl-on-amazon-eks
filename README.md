# SQL-based ETL with Spark on EKS

We introduce a quality-aware design to increase data processing productivity, by leveraging an open-source [Arc data framework](https://arc.tripl.ai/) for a user-centered declarative ETL solution. We take considerations of the needs and expected skills from customers in data analytics, and accelerate their interaction with ETL practice in order to foster simplicity, while maximizing efficiency.

The sample provides two ways of running the solution shown in the architecture diagram:
1. Spark on EKS by Argo Workflows tool
2. [EMR on EKS](https://aws.amazon.com/emr/features/eks/) 

![](/spark-on-eks/images/two_architecture.png)

### Test job in Jupyter
![](/spark-on-eks/images/run_jupyter.gif)


### Test Spark Driver self-recovery (100% spot)
![](/spark-on-eks/images/driver_interruption_test.gif)

### Submit Spark job by Argo tool
![](/spark-on-eks/images/submit_job_in_argo.gif)


## Prerequisite
Running the sample solution on a local machine, you should have the following prerequisites:
1. Python 3.6 or later. Download Python [here](https://www.python.org/downloads/).
2. AWS CLI version 1.
  Windows: [MSI installer](https://docs.aws.amazon.com/cli/latest/userguide/install-windows.html#install-msi-on-windows)
  Linux, macOS or Unix: [Bundled installer](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html#install-macosos-bundled)
3. AWS CLI is configured to communicate with services in your deployment account. Otherwise, either set your profile by `export AWS_PROFILE=<your_aws_profile>` , or run the following configuration to setup your AWS account access.
```bash
aws configure
```  
If you don’t want to install anything on your computer, use [AWS CloudShell](https://aws.amazon.com/cloudshell/), a browser-based shell that makes it easy to run scripts with the AWS Command Line Interface (AWS CLI).

## Clone the project
Download the sample code either to your computer or to your [AWS CloudShell Console](https://console.aws.amazon.com/cloudshell/home?region=us-east-1).

```bash
git clone https://github.com/aws-samples/sql-based-etl-on-amazon-eks.git
cd sql-based-etl-on-amazon-eks
```

## Deploy Infrastructure

The provisining takes about 30 minutes to complete. See the `troubleshooting` section if you have any problem during the deployment. 

The example solution provides two options to submit ETL jobs. See the detailed deployment instruction:

1. [Spark on EKS](/spark-on-eks/README.md)
2. [EMR on EKS](/emr-on-eks/README.md)


## Troubleshooting
1. If you see the error `Credentials were refreshed, but the refreshed credentials are still expired` in AWS CloudShell, click **Actions** button, and create a `New tab`.

2. If you see the issue `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)`, most likely it means no default certificate authority for your Python installation on OSX. Refer to the [answer](https://stackoverflow.com/questions/52805115/0nd) installing `Install Certificates.command` should fix your local environment. Otherwise, use [Cloud9](https://aws.amazon.com/cloud9/details/) to deploy the CDK instead.


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE.txt) file.