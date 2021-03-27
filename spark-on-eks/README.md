# SQL-based ETL with Spark on EKS
This is a project for a solution - SQL based ETL with a declarative framework powered by Apache Spark. 

We introduce a quality-aware design to increase data processing productivity, by leveraging an open-source [Arc data framework](https://arc.tripl.ai/) for a user-centered declarative ETL solution. Additionally, we take considerations of the needs and expected skills from customers in data analytics, and accelerate their interaction with ETL practice in order to foster simplicity, while maximizing efficiency.

## Overview
![](/images/architecture.png)

### Test job in Jupyter
![](/images/run_jupyter.gif)

### Submit Spark job in Argo
![](/images/submit_job_in_argo.gif)

### Submit Spark job in k8s
![](images/submit_native_spark.gif)

#### Table of Contents
* [Prerequisites](#Prerequisites) 
* [Deploy Infrastructure](#Deploy-Infrastructure)
  * [Prepare Deployment](#Prepare-deployment)
  * [Deploy via CloudFormation template](#Deploy-via-CloudFormation-template)
  * [Deploy via CDK](#Deploy-via-CDK)
* [Troubleshooting](#Troubleshooting)
* [Post Deployment](#Post-Deployment)
  * [Install kubernetes tool](#Install-kubernetes-tool)
  * [Connect to EKS](#Connect-to-EKS-cluster)
  * [Test Arc ETL job in Jupyter](#Test-Arc-ETL-job-in-Jupyter)
  * [Submit & Orchestrate Arc job](#Submit--orchestrate-Arc-ETL-job)
    * [Submit a job on Argo UI](#Submit-a-job-on-Argo-UI)
    * [Submit a job via Argo CLI](#Submit-a-job-via-Argo-CLI)
  * [Submit a native Spark job](#Submit-a-native-Spark-job)
    * [Submit a job via kubectl](#Submit-a-job-via-kubectl)
    * [Self-recovery test](#Self-recovery-test)
    * [Cost savings with spot instance](#Check-Spot-instance-usage-and-cost-savings)
    * [Auto scaling & Dynamic resource allocation](#Explore-EKS-features-Auto-Scaling-across-Multi-AZ-and-Spark's-Dynamic-Allocation-support)
* [Useful Commands](#Useful-Commands)  
* [Clean Up](#clean-up)
* [Security](#Security)
* [License](#License)

## Prerequisites 
1. Python 3.6 or later. You can find information about downloading and installing Python [here](https://www.python.org/downloads/).
2. AWS CLI version 1.
  Windows: [MSI installer](https://docs.aws.amazon.com/cli/latest/userguide/install-windows.html#install-msi-on-windows)
  Linux, macOS or Unix: [Bundled installer](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html#install-macosos-bundled)

## Deploy Infrastructure

This project is set up like a standard Python project. The `source/cdk.json` file tells where the application entry point is. 
 
The provisining takes about 30 minutes to complete. See the `troubleshooting` section if you have a problem during the deployment. There are two ways to deploy the solution, either by CloudFormation template or by [AWS Cloud Development Kit (AWS CDK)](https://docs.aws.amazon.com/cdk/latest/guide/home.html).

### Prepare deployment
Assume your AWS CLI can communicate with services in your deployment account. Otherwise, either set your profile by `export AWS_PROFILE=<your_aws_profile>` , or run the following configuration to setup your AWS account access.

```bash
aws configure
```
* Clone the project

```bash
git clone https://github.com/aws-samples/sql-based-etl-on-eks.git
cd sql-based-etl-on-eks
```

[*^ back to top*](#Table-of-Contents)
### Deploy via CloudFormation template

You can customize the solution then generate the CloudFormation template in your region.

```bash
export DIST_OUTPUT_BUCKET=my-bucket-name # existing bucket where CFN template will reside
export SOLUTION_NAME=sql-based-etl
export VERSION=v1.0.0 # version number for the solution
export AWS_REGION=your-region

./deployment/build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION $DIST_OUTPUT_BUCKET

# Upload CFN templates to your S3 bucket
aws s3 cp ./deployment/global-s3-assets/ s3://$DIST_OUTPUT_BUCKET/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control
aws s3 cp ./deployment/regional-s3-assets/ s3://$DIST_OUTPUT_BUCKET/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control

echo "paste the link to a web browser to launch the CloudFormation templalte: https://console.aws.amazon.com/cloudformation/home?region=$AWS_REGION#/stacks/new?stackName=SparkOnEKS&templateURL=https://$DIST_OUTPUT_BUCKET.s3.amazonaws.com/$SOLUTION_NAME/$VERSION/SparkOnEKS.template"
```
The template takes 2 optional parameters:

* Option1: Deploy with default values.
* Option2: Fill in the parameter `jhubuser` if you want to setup a customized username for Jupyter login. 
* Option3: If ETL your own data, fill in the parameter `datalakebucket` with your S3 bucket.
`NOTE: the S3 bucket must be in the same region as the deployment region.`


[*^ back to top*](#Table-of-Contents)
### Deploy via AWS CDK

Alternatively, you can spin up the solution infrastructure via [AWS Cloud Development Kit](https://cdkworkshop.com/), in short, AWS CDK. The CDK deployment requires Node.js (>= 10.3.0) and AWS CDK Toolkit. To install Node.js visit the [node.js](https://nodejs.org/en/) website. To install the CDK toolkit, follow the [instruction](https://cdkworkshop.com/15-prerequisites/500-toolkit.html). 
 
Two reasons to deploy the solution resources by AWS CDK:
1. CDK provides local development,debug experience and fail fast.
2. Convenient to customize the solution with a quicker test response. For example remove a nested stack CloudFront and enable TLS in ALB.
 
```bash
python3 -m venv .env
```
If you are in a Windows platform, you would activate the virtualenv like this:
 
```
% .env\Scripts\activate.bat
```
After the virtualenv is created, you can use the followings to activate your virtualenv and install the required dependencies.
 
```bash
source .env/bin/activate
pip install -e source
```
 
* Option1: Deploy with default (recommended)

```bash
cd source
cdk deploy
```
* Option2: Jupyter login with a customized username

```bash
cd source
cdk deploy --parameters jhubuser=<random_login_name>
```
* Option3: If ETL your own data, use the parameter datalakebucket
Ensure your S3 bucket is in the same region as the deployment region.

```bash
cd source
cdk deploy --parameters jhubuser=<random_login_name> --parameters datalakebucket=<existing_datalake_bucket>
```

[*^ back to top*](#Table-of-Contents)
## Troubleshooting

1. If you see the issue `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)`, most likely it means no default certificate authority for your Python installation on OSX. Refer to the [answer](https://stackoverflow.com/questions/52805115/0nd) installing `Install Certificates.command` should fix your local environment. Otherwise, use [Cloud9](https://aws.amazon.com/cloud9/details/) to deploy the CDK instead.

2. If an error appears during the CDK deployment: `Failed to create resource. IAM role’s policy must include the "ec2:DescribeVpcs" action`. The possible causes are: 1) you have reach the quota limits of Amazon VPC resources per Region in your AWS account. Please deploy to a different region or a different account. 2) based on this [CDK issue](https://github.com/aws/aws-cdk/issues/9027), you can retry without any changes, it will work. 3) If you are in a branch new AWS account, manually delete the AWSServiceRoleForAmazonEKS from IAM role console before the deployment. 


[*^ back to top*](#Table-of-Contents)
## Post Deployment

### Install kubernetes tool
Go to [AWS CloudShell](https://console.aws.amazon.com/cloudshell/), select your **region** the solution was deployed. Run the command: 
 ```bash
 curl https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-eks/master/deployment/setup_cmd_tool.sh | bash
 ```
NOTE: each CloudShell session will timeout after idle for 20 minutes, the installation may need to run again.

Alternatively, if AWS CloudShell is not avaiable in your region, simply run the post deployment commands in a local machine with a command line tool installed, for example:
 ```bash
 ./deployment/setup_cmd_tool.sh
 ```
 
### Connect to EKS cluster
In the same CloudShell session or your local machine, run a configure command that can be found on [CloudFormation Output](https://console.aws.amazon.com/cloudformation/) in Stack SparkOnEKS. It looks like this:
```bash
aws eks update-kubeconfig --name <eks_name> --region <region> --role-arn <role_arn>

# check the connection
kubectl get svc
```

### Test Arc ETL job in Jupyter
The sample [contacts data](/deployment/app_code/data/) is not real data. They are generated programatically by a [python script](https://raw.githubusercontent.com/cartershanklin/hive-scd-examples/master/merge_data/generate.py).

![](/images/fake_data.gif)

1. Login to Jupyter WebUI found at [CloudFormation Output](https://console.aws.amazon.com/cloudformation/).

  * username - `sparkoneks`, or your login name specified. 
  * password - get password in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/)
  ```bash
  JHUB_PWD=$(kubectl -n jupyter get secret jupyter-external-secret -o jsonpath="{.data.password}" | base64 --decode)
  echo -e "\nJupyter password: $JHUB_PWD"
  ```
  NOTE: The Jupyter session will end if it is inactive for 30 minutes. You may lose your work, if it hasn't been saved back to a Git repository. Or you can download it to your computer. The download capability is configurable and could be disabled in order to improve the data security.

2. Open a sample notebook `sql-based-etl/source/example/scd2-job.ipynb` on your JupyterHub instnace, which is cloned from the current git repo.

  This example will create a table to support [Slowly Changing Dimension Type 2](https://www.datawarehouse4u.info/SCD-Slowly-Changing-Dimensions.html) format. You will get hands-on experience on SQL-based ETL by walking through the incremental data load in Data Lake.

  To demonstrate the best practice in DataDevOps, your Jupyter instance clones the latest source artifact from this Git repository each time when you login. In real practice, you must check-in all changes to a source repository, in order to save and trigger ETL pipelines.

3. Execute each block and observe the result. Change SQL scripts on the notebook if you like.
4. The sample notebook outputs a `Delta Lake` table. Run a query in [Athena](https://console.aws.amazon.com/athena/) console to check if it is a SCD2 type. 
    ```sql
    SELECT * FROM default.deltalake_contact_jhub WHERE id=12
    ```
[*^ back to top*](#Table-of-Contents)

### Submit & orchestrate Arc ETL job
* Check your EKS connection in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/). If no access, see the section:[Connect to EKS cluster](#Connect-to-EKS-cluster)
```bash
kubectl get svc
```
* Go to Argo website found in the Cloudformation output. Run `argo auth token` command in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/) to get a login token, and paste it to Argo.

#### Submit a job on Argo UI

  Click `SUBMIT NEW WORKFLOW` button, replace content by the followings, then `SUBMIT`. Click a pod (dot) to check application logs.

  ```yaml
  apiVersion: argoproj.io/v1alpha1
  kind: Workflow
  metadata:
    generateName: nyctaxi-job-
    namespace: spark
  spec:
    serviceAccountName: arcjob
    entrypoint: nyctaxi
    templates:
    - name: nyctaxi
      dag:
        tasks:
          - name: step1-query
            templateRef:
              name: spark-template
              template: sparkLocal
              clusterScope: true   
            arguments:
              parameters:
              - name: jobId
                value: nyctaxi  
              - name: tags
                value: "project=sqlbasedetl, owner=myowner, costcenter=66666"  
              - name: configUri
                value: https://raw.githubusercontent.com/tripl-ai/arc-starter/master/examples/kubernetes/nyctaxi.ipynb
              - name: parameters
                value: "--ETL_CONF_DATA_URL=s3a://nyc-tlc/trip*data \
                --ETL_CONF_JOB_URL=https://raw.githubusercontent.com/tripl-ai/arc-starter/master/examples/kubernetes"
  ```

#### Submit a job via Argo CLI 

Let's submit the scd2 notebook that was tested earlier. To mock up a real-world scenario, we have break it down to 3 notebook files, ie. 3 ETL jobs, stored in `deployment/app_code/job/`. It only takes approx. 4 minutes to complte the entire data pipeline.

* Check EKS connection in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/). If no access, follow the first step in [Post Deployment](#Post-Deployment)
```bash
kubectl get svc
```
* Replace the placeholder by an S3 bucket name found in [CloudFormation Console](https://console.aws.amazon.com/cloudformation). Run the command by AWS CloudShell then check progress in Argo UI.
```bash
app_code_bucket=<your_codeBucket_name>
argo submit https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-eks/master/source/example/scd2-job-scheduler.yaml -n spark --watch  -p codeBucket=$app_code_bucket
```
![](/images/3-argo-job-dependency.png)

* Query the table in [Athena](https://console.aws.amazon.com/athena/) to see if it has the same outcome as your testing in Jupyter. 

```sql
SELECT * FROM default.contact_snapshot WHERE id=12
```
[*^ back to top*](#Table-of-Contents)

### Submit a native Spark job

Reuse the Arc docker image to run a native Spark application, defined by k8s's CRD [Spark Operator](https://operatorhub.io/operator/spark-gcp). It saves efforts on DevOps operation, as the way of deploying Spark application follows the same declarative approach in k8s. It is consistent with other business applications CICD deployment processes.
  The example demonstrates:
  * Save cost with [Amazon EC2 Spot instance](https://aws.amazon.com/ec2/spot/) type
  * Dynamically scale a Spark application - via [Dynamic Resource Allocation](https://spark.apache.org/docs/3.0.0-preview/job-scheduling.html#dynamic-resource-allocation)
  * Self-recover after losing a Spark driver
  * Monitor a job on Spark WebUI

#### Submit a job via kubectl 
* Execute the command on [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home?region=us-east-1).

```bash
kubectl create -n spark configmap special-config --from-literal=codeBucket=<your_codeBucket_name>
kubectl apply -f https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-eks/master/source/example/native-spark-job-scheduler.yaml

# watch the progress in EKS
kubectl get pod -n spark

# modify the schedule file locally if you like, then rerun
kubectl delete -f source/example/native-spark-job-scheduler.yaml
kubectl apply -f source/example/native-spark-job-scheduler.yaml

# watch job progress on SparkUI
kubectl port-forward word-count-driver 4040:4040 -n spark
# go to `localhost:4040` from your web browser
```

[*^ back to top*](#Table-of-Contents)
#### Self-recovery test
In Spark, driver is a single point of failure in data processing. If driver dies, all other linked components will be discarded too. Outside of k8s, it requires extra effort to set up a job rerun, in order to manage the situation, however It is much simpler in EKS. 

* The native Spark job takes approx. 10 minutes to finish. Let's test its fault tolerance by kill the driver first: 

```bash
kubectl delete pod -n spark word-count-driver --force
# has the driver come back instantly?
kubectl get po -n spark
```
* Now kill one of executors: 

```bash
# replace the example pod name by yours
kubectl delete -n spark pod <example:amazon-reviews-word-count-51ac6d777f7cf184-exec-1> --force
# has it come back with a different number suffix? 
kubectl get po -n spark
```

[*^ back to top*](#Table-of-Contents)
#### Check Spot instance usage and cost savings
Go to [Spot Request console](https://console.aws.amazon.com/ec2sp/v2/) -> Saving Summary, to find out how much running cost you just saved.

#### Explore Other features: Auto Scaling across Multi-AZ, and Spark's Dynamic Allocation support

This job will end up with 20 Spark executors/pods on around 7 spot EC2 instances. It takes 10 minutes to complete. Based on the resource allocation defined in the job manifest file, it runs approx. 3 executors per EC2 spot instance. As soon as the job is kicked in, you will see the autoscaling is triggered within seconds. It scales the Spark cluster from 0 to 10 executors, then reduce to 3 executor as only 1 spot node in the EKS intially. Eventualy, the Spark cluster will scale to 20 executors, driven by the DynamicAllocation capability in Spark.

The auto-scaling is configured to be balanced within two AZs. Depending on your business requirement, you can fit the ETL job into a single AZ if needed.

```bash
kubectl get node --label-columns=lifecycle,topology.kubernetes.io/zone
kubectl get pod -n spark
```
![](/images/4-auto-scaling.png)

[*^ back to top*](#Table-of-Contents)
## Useful Commands
 * `argo submit source/example/nyctaxi-job-scheduler.yaml`  submit a spark job via Argo
 * `argo list --all-namespaces`                       show all jobs scheduled via Argo
 * `kubectl get pod -n spark`                         list running Spark jobs
 * `kubectl delete pod --all -n spark`                delete all Spark jobs
 * `kubectl apply -f source/app_resources/spark-template.yaml` create a reusable Spark job template

[*^ back to top*](#Table-of-Contents)
## Clean up
Go to the repo's root directory, and run the clean up script.

```bash
cd sql-based-etl
./deployment/delete_all.sh
```
[*^ back to top*](#Table-of-Contents)
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE.txt) file.