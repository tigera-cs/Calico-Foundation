
# Introduction to training labs infrastructure


Training labs demonstrate the working of Calico Enterprise features including Policy Recommendations, Policy Management, Custom Alerting and Compliance Reporting.

– Its a good kick-start activity to understand Calico Enterprise capabilities.

## Requirements

Kubernetes or Openshift cluster with sufficient CPU, storage and memory

## Lab Hosts

 IP Address Node/Purpose

 10.0.0.10 Kubernetes Master

 10.0.0.11 Kubernetes Worker 01

 10.0.0.12 Kubernetes Worker 02

Note : These IP addresses may change in case of Openshift Deployments, check using `oc get nodes -o wide`
## Accessing ttyd and Tigera Manager UI

Make sure you have the username and password to access ttyd prompt (ttyd access is configured only in case of standard k8s deployments and not oc)

ttyd access - http://<Master Node Public IP>:31000

Enter the token provided

Tigera Manager - https://<Master Node Public IP>:30003  / For Openshift https://loadbalancer-ip:9443

## Training lab infrastructure layout

The infrastructure directory consists of a three-tier application deployment consisting of front-end, back-end, database and relevant services. 3 sets of deployments are created in development, staging and production namespaces accordingly along with application hardening Network Policies and Global Network Policies. The following script triggers the creation of infrastructure.

```
./create-infrastructure.sh
```

## Example - Getting details of application in development namespace

kubectl get pods -n development -o wide  / oc get pods -n development -o wide

kubectl get svc -n development  / oc get svc -n development

## Labs

Lab1: Policy Recommendations


Lab2: Custom Alerts


Lab3: Auditing & Compliance Reporting


Lab4: Threat Detection and alerting

#### Note : For Openshift deployments you can opt using `oc` as client to access the cluster.


