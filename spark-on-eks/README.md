# SQL-based ETL with Spark on EKS
A project for a solution - SQL based ETL with a declarative framework powered by Apache Spark. 

## Spark on EKS Overview
![](images/architecture.png)

### Submit ETL job in k8s
![](images/submit_native_spark.gif)

#### Table of Contents
* [Prerequisites](#Prerequisites) 
* [Deploy Infrastructure](#Deploy-Infrastructure)
* [Post Deployment](#Post-Deployment)
  * [Install kubernetes tool](#Install-kubernetes-tool)
  * [Connect to EKS](#Connect-to-EKS-cluster)
  * [Test ETL job in Jupyter](#Test-Arc-ETL-job-in-Jupyter)
  * [Arc ETL job](#Arc-ETL-job)
    * [Submit job on Argo UI](#Submit-job-on-Argo-UI)
    * [Submit job by Argo CLI](#Submit-job-by-Argo-CLI)
  * [Native Spark job](#submit-native-Spark-job-with-spark-operator)
    * [Submit job by kubectl](#Submit-job-by-kubectl)
    * [Self-recovery test](#Self-recovery-test)
    * [Cost savings with spot instance](#Check-Spot-instance-usage-and-cost-savings)
    * [Auto scaling & Dynamic resource allocation](#Autoscaling---dynamic-allocation-support)
* [Useful Commands](#Useful-Commands)  
* [Clean Up](#clean-up)

## Prerequisites 

1. AWS CLI is configured to communicate with services in your deployment account. Either set your profile by `export AWS_PROFILE=<your_aws_profile>` , or run `aws configure`.
2. [AWS CloudShell](https://console.aws.amazon.com/cloudshell/) is available in your deployment **region**. Otherwise, run all post deployment commands in a local computer.

## Deploy Infrastructure
The provisining takes about 30 minutes to complete. 

```bash
git clone https://github.com/aws-samples/sql-based-etl-on-amazon-eks.git
cd sql-based-etl-on-amazon-eks/spark-on-eks
```

  |   Region  |   Launch Template |
  |  ---------------------------   |   -----------------------  |
  |  ---------------------------   |   -----------------------  |
  **Choose Your Region**| [![Deploy to AWS](images/00-deploy-to-aws.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?stackName=SparkOnEKS&templateURL=https://solutions-test-reference.s3.amazonaws.com/sql-based-etl-with-apache-spark-on-amazon-eks/v1.0.0/SparkOnEKS.template) 

* Option1: Deploy with default (recommended). The default region is us-east-1. 
To launch in a different AWS Region, use the Region selector in the console navigation bar. 
* Option2: Fill in the parameter `jhubuser` if you want to setup a customized username for Jupyter login. 
* Option3: If ETL your own data, input the parameter `datalakebucket` with your S3 bucket. 
`NOTE: the S3 bucket must be in the same region as the deployment region.`

You can customize the solution, then generate the CFN in your region: 
```bash
export BUCKET_NAME_PREFIX=<my-bucket-name> # bucket where customized code will reside
export AWS_REGION=<your-region>
export SOLUTION_NAME=sql-based-etl
export VERSION=v1.0.0 # version number for the customized code

./deployment/build-s3-dist.sh $BUCKET_NAME_PREFIX $SOLUTION_NAME $VERSION

# create the bucket where customized code will reside
aws s3 mb s3://$BUCKET_NAME_PREFIX-$AWS_REGION --region $AWS_REGION

# Upload deployment assets to the S3 bucket
aws s3 cp ./deployment/global-s3-assets/ s3://$BUCKET_NAME_PREFIX-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control
aws s3 cp ./deployment/regional-s3-assets/ s3://$BUCKET_NAME_PREFIX-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control

echo "In web browser, paste the URL to launch the template: https://console.aws.amazon.com/cloudformation/home?region=$AWS_REGION#/stacks/quickcreate?stackName=SparkOnEKS&templateURL=https://$BUCKET_NAME_PREFIX-$AWS_REGION.s3.amazonaws.com/$SOLUTION_NAME/$VERSION/SparkOnEKS.template"
```

[*^ back to top*](#Table-of-Contents)
## Post Deployment

### Install kubernetes tool
Go to [AWS CloudShell](https://console.aws.amazon.com/cloudshell/), select your deployment **region** and run the command: 
 ```bash
 curl https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/spark-on-eks/deployment/setup_cmd_tool.sh | bash
 ```
NOTE: each CloudShell session will timeout after idle for 20 minutes, the installation may need to run again.

Alternatively, if AWS CloudShell is not avaiable in your region, simply run the post deployment commands in your computer:
 ```bash
 ./deployment/setup_cmd_tool.sh
 ```

[*^ back to top*](#Table-of-Contents)
### Connect to EKS cluster
In the same CloudShell session or your local machine, run an EKS configure command that can be found on the [CloudFormation Console](https://console.aws.amazon.com/cloudformation/) in Stack SparkOnEKS. It looks like this:
```bash
aws eks update-kubeconfig --name <eks_name> --region <region> --role-arn <role_arn>

# check the connection
kubectl get svc
```

[*^ back to top*](#Table-of-Contents)
### Test Arc ETL job in Jupyter
The sample [contacts data](/deployment/app_code/data/) is not real data. They are generated programatically by a [python script](https://raw.githubusercontent.com/cartershanklin/hive-scd-examples/master/merge_data/generate.py).

![](images/fake_data.gif)

1. Login to a Jupyter WebUI found at [CloudFormation Output](https://console.aws.amazon.com/cloudformation/).

  * username - `sparkoneks`, or your login name specified. 
  * password - get password in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/)
  ```bash
  JHUB_PWD=$(kubectl -n jupyter get secret jupyter-external-secret -o jsonpath="{.data.password}" | base64 --decode)
  echo -e "\nJupyter password: $JHUB_PWD"
  ```

2. Open a sample notebook `source/example/notebook/scd2-job.ipynb` on your JupyterHub instnace, which is cloned from the current git repo.

  This example will create a table to support [Slowly Changing Dimension Type 2](https://www.datawarehouse4u.info/SCD-Slowly-Changing-Dimensions.html) format. You will get hands-on experience on SQL-based ETL by walking through the incremental data load in Data Lake.

  To demonstrate the best practice in DataDevOps, your Jupyter instance clones the latest source artifact from this Git repository each time when you login. In real practice, you must check-in all changes to a source repository, in order to save and trigger ETL pipelines.

3. Execute each block and observe the result.
4. The sample notebook outputs a `Delta Lake` table. Run a query in [Athena console](https://console.aws.amazon.com/athena/) to check if it is a SCD2 type. 
  ```sql
  SELECT * FROM default.deltalake_contact_jhub WHERE id=12
  ```

[*^ back to top*](#Table-of-Contents)
### ARC ETL job
* Check your EKS connection in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/). If no access, see the section:[Connect to EKS cluster](#Connect-to-EKS-cluster)
```bash
kubectl get svc
```
* Go to Argo website found in the CloudFormation console. Run `argo auth token` command in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/) to get a login token, and paste it to Argo.

[*^ back to top*](#Table-of-Contents)
#### Submit job on Argo UI
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

[*^ back to top*](#Table-of-Contents)
#### Submit job by Argo CLI 
Let's submit the scd2 notebook tested earlier. To mock up a real-world scenario, we have break it down to 3 notebook files, ie. 3 ETL jobs, stored in `deployment/app_code/job/`. 

* Find the S3 bucket name in [CloudFormation console](https://console.aws.amazon.com/cloudformation). Run the command in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/) then check progress in Argo UI.
```bash
app_code_bucket=<your_codeBucket_name>
argo submit https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/spark-on-eks/source/example/scd2-job-scheduler.yaml -n spark --watch  -p codeBucket=$app_code_bucket
```
![](images/3-argo-job-dependency.png)

* Query the table in [Athena](https://console.aws.amazon.com/athena/) to see if it has the same outcome as the test in Jupyter earlier. 

```sql
SELECT * FROM default.contact_snapshot WHERE id=12
``` 

[*^ back to top*](#Table-of-Contents)
### Submit native Spark job with Spark operator

Reuse the Arc docker image (Spark 3.0.2) to run a native Spark application, defined by k8s's CRD [Spark Operator](https://operatorhub.io/operator/spark-gcp). It saves efforts on DevOps operation, as the way of deploying Spark application follows the same declarative approach in k8s. It is consistent with other business applications CICD deployment processes.
  The example demonstrates:
  * Save cost with [Amazon EC2 Spot instance](https://aws.amazon.com/ec2/spot/) type
  * Dynamically scale a Spark application - via [Dynamic Resource Allocation](https://spark.apache.org/docs/3.0.0-preview/job-scheduling.html#dynamic-resource-allocation)
  * Self-recovery after losing a Spark driver
  * Monitor a job on Spark WebUI

[*^ back to top*](#Table-of-Contents)
#### Submit job by kubectl
* Execute the command in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/). Replace the codeBucket placeholder by your S3 bucket found on the [CloudFormation Output](https://console.aws.amazon.com/cloudformation/home?region=us-east-1). Then submit the job to EKS.
```bash
kubectl create -n spark configmap special-config --from-literal=codeBucket=<your_codeBucket_name>
kubectl apply -f https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/spark-on-eks/source/example/native-spark-job-scheduler.yaml

# OR submit the job from your computer
kubectl apply -f source/example/native-spark-job-scheduler.yaml

# watch the progress in EKS
kubectl get pod -n spark

# watch job progress on SparkUI
kubectl port-forward word-count-driver 4040:4040 -n spark
# go to `localhost:4040` from your web browser
```

[*^ back to top*](#Table-of-Contents)
#### Self-recovery test
In Spark, driver is a single point of failure in data processing. If driver dies, all other linked components will be discarded too. Outside of Kubernetes, it requires extra effort to set up a job rerun, in order to provide the fault tolerance capability, however It is much simpler in Amazon EKS. 

The native Spark job takes approx. 10 minutes to finish. Let's test the self-recovery against the running Spark cluster.

* Firstly, manually kill the EC2 instance running the Spark driver:
```bash
Kubectl describe pod word-count-driver -n spark
# delete the EC2 server found in the description
kubectl delete node <ec2_host_name>
# Did your driver come back in seconds?
kubectl get pod -n spark

```
See the demonstration below, which simulates the Spot interruption scenario: 
![](/spark-on-eks/images/driver_interruption_test.gif)

* Now kill one of executors: 

```bash
# replace the example pod name by yours
kubectl delete -n spark pod <example:amazon-reviews-word-count-51ac6d777f7cf184-exec-1> --force
# has it come back with a different number suffix? 
kubectl get pod -n spark
```

[*^ back to top*](#Table-of-Contents)
#### Check Spot instance usage and cost savings
Go to [Spot Request console](https://console.aws.amazon.com/ec2sp/v2/) -> Saving Summary, to find out how much running cost you just saved.

#### Autoscaling & Dynamic Allocation support

The job ends up with 20 Spark executors/pods on 7 spot EC2 instances. It takes 10 minutes to complete. Based on the resource allocation defined by the job manifest file, it runs approx. 3 executors per EC2 spot instance. 

Once the job is kicked in, you will see the autoscaling is triggered within seconds. It scales the Spark cluster from 0 to 10 executors. Eventually, the Spark cluster scales to 20 executors, driven by the DynamicAllocation capability in Spark.

The auto-scaling is configured to be balanced within two AZs. Depending on your business requirement, you can fit the ETL job into a single AZ if needed.

```bash
kubectl get node --label-columns=lifecycle,topology.kubernetes.io/zone
kubectl get pod -n spark
```
![](images/4-auto-scaling.png)

[*^ back to top*](#Table-of-Contents)
## Useful Commands
 * `argo submit source/example/nyctaxi-job-scheduler.yaml`  submit a spark job via Argo
 * `argo list --all-namespaces`                       show all jobs scheduled via Argo
 * `kubectl get pod -n spark`                         list running Spark jobs
 * `kubectl delete pod --all -n spark`                delete all Spark jobs
 * `kubectl apply -f source/app_resources/spark-template.yaml` create a reusable Spark job template

[*^ back to top*](#Table-of-Contents)
## Clean up
Go to the repo's root directory, and run the clean-up script. 

```bash
cd sql-based-etl-on-amazon-eks/spark-on-eks
./deployment/delete_all.sh
```
Follow the instruction below to delete the remaining resources on the AWS management console if needed.
1.  Sign in to the AWS CloudFormation console. 
2.  Select this solution’s installation stack called SparkOnEKS.
3.  Choose Delete.
