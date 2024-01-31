<!--
SPDX-FileCopyrightText: 2021 Amazon.com, Inc. or its affiliates.

SPDX-License-Identifier: MIT-0
-->

# Arc ETL framework on EMR on EKS
AWS Launched [EMR on EKS](https://aws.amazon.com/emr/features/eks/) and this sample demonstrates an end-to-end process to provision an EKS cluster, execute a Spark ETL job defined as a [jupyter notebook](green_taxi_load.ipynb) using [Arc Framework](https://arc.tripl.ai/getting-started/).

# Provisioning
1. Open AWS CloudShell in us-east-1: [link to AWS CloudShell](https://console.aws.amazon.com/cloudshell/home?region=us-east-1)
2. Run the following command to provision a new EKS cluster `eks-cluster` backed by Fargate and build a virtual EMR cluster `emr-on-eks-cluster` 
    ```bash
    curl https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/emr-on-eks/provision.sh | bash
    ```
3. Once provisioning is complete (~20 min), run the following command to submit a new Spark job on the virtual EMR cluster:
    ```bash
    curl https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/emr-on-eks/submit_arc_job.sh | bash
    ```
    The sample job will create an output S3 bucket, load the [TLC green taxi trip records](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page) from public `s3://nyc-tlc/csv_backup/green_tripdata*.csv`, apply schema, convert it into Parquet and store it in the output S3 bucket.

    The job is defined as a [jupyter notebook green_taxi_load.ipynb](green_taxi_load.ipynb) using [Arc Framework](https://arc.tripl.ai/getting-started/) and the applied schema is defined in [green_taxi_schema.json](green_taxi_schema.json)


## AWS Resources
* EKS cluster: [link to AWS Console](https://console.aws.amazon.com/eks/home?region=us-east-1#/clusters/eks-cluster)
* Virtual EMR Clusters and jobs: [link to AWS Console](https://console.aws.amazon.com/elasticmapreduce/home?region=us-east-1#virtual-cluster-list:)
* CloudWatch EMR job logs: [link to AWS Console](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Feks$252Feks-cluster$252Fjobs)
* S3 buckets - navigate to the output S3 bucket: [link to AWS Console](https://s3.console.aws.amazon.com/s3/home?region=us-east-1)

## EKS Resources
To review the execution process, run: 
```
kubectl get po -n emr
```

# Cleanup
To clean up resources, run:
```bash
curl https://raw.githubusercontent.com/aws-samples/sql-based-etl-on-amazon-eks/main/emr-on-eks/deprovision.sh | bash
```



That's it!
