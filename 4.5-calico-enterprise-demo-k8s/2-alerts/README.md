# Lab 2: Creating Alerts using Calico Enterprise

Lab objective: Calico Enterprise enables a user to create customized Alerts in order to get notified on specific events happening on the deployed workloads.

Calico Enterprise supports alerts on the following data sets:

- Audit logs
- DNS logs
- Flow logs

Note: Make sure you are working in `2-alerts` directory.

## Lab tasks

1. Configure the flow logs aggregation kind in felix resource, Use the below command to edit the resource and add the parameter `flowLogsFileAggregationKindForAllowed: 1` to the end of spec section.
```
kubectl edit felixconfigurations default
```
We need to turn down the aggregation of flow logs sent to Elasticsearch for configuring threat feeds. If you do not adjust flow logs, Calico Enterprise aggregates over the external IPs for allowed traffic, and alerts will not provide pod-specific results. Here we are setting the field flowLogsFileAggregationKindForAllowed to value "1".

2. Execute the `generate-alerts.sh` script that should do the prerequisites for generating the Alerts and it also triggers the `trigger-threatdef-features.py` responsible for setting up alerts and generating relevant traffic . This should create DNS, flows, flows[lateral movement], flows [cloud API], audit [privileged access] alerts.
```
./generate-alerts.sh
```

After few minutes alert should be visible under Alerts panel on the Tigera Manager. Entries should look as follows:
![sample-alerts](img/alerts.png)

