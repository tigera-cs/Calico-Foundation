# Lab 3.3: Policy Audit Report

Lab objective : To assess your clusters against changes in network policy w.e.f Creation, Modification and Deletion in order to track down the policy that caused changes in the environment.


Lab tasks

1. Configure compliance-reporter-pod manifest.

```
./configure-cr.sh
```
The above script is responsible to update the compliance-reporter-pod.yaml manifest with appropriate reporter-token secret name, report name and report start time in UTC 3339 format



2. In the following example, creates a GlobalReport that results in a daily policy audit report for policies that are applied to endpoints in the development, staging, production namespace.

```
kubectl apply -f hourly-policy-globalreport.yaml
```


3. Apply the compliance-reporter-pod.yaml manifest to manually run the reports. Make sure the below manifest is configured with appropriate reporter-token secret name, report name and report start time in UTC 3339 format

```
kubectl apply -f compliance-reporter-pod.yaml
```
The output on the Tigera Manager should look as follows:

![policy-report-sample](img/policy-report.png)


Make sure you cleanup the infrastructure once you have completed the lab. We will be deploying other set of applications for the next lab

```
./cleanup.sh
```

