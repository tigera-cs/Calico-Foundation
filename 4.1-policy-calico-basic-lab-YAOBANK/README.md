## 4.1. Policy: Basic Calico Network Policy Lab
This is the first lab of a series of labs focusing on Calico k8s network policy. Throughout this lab we will deploy and test our first Calico k8s network policy. 
In this lab we will:
4.1.1. Verify connectivity from customer pod
4.1.2. Apply a simple Calico Policy

### 4.1.0. Before you begin

Throughout this lab, we will be using the yaobank app we deployed in Lab1.
If you haven't done so, please go back and complete Lab1.


### 4.1.1. Verify connectivity from CentOS pod

Let's start with checking the ip address information of our deployment.

```
kubectl get pod -n yaobank -o wide
NAME                        READY   STATUS    RESTARTS   AGE   IP              NODE           NOMINATED NODE   READINESS GATES
customer-84c7855fd4-55r26   1/1     Running   0          79m   10.48.110.14    ip-10-0-0-11   <none>           <none>
database-56fb9496bb-mdch5   1/1     Running   0          78m   10.48.194.175   ip-10-0-0-12   <none>           <none>
summary-7f89fbcc7c-tsqjz    1/1     Running   0          89m   10.48.194.174   ip-10-0-0-12   <none>           <none>
summary-7f89fbcc7c-vl9px    1/1     Running   0          67m   10.48.177.96    ip-10-0-0-10   <none>           <none>
```

```
ubuntu@ip-10-0-0-11:~$ kubectl get svc -n yaobank
NAME       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
customer   NodePort    10.49.46.93    <none>        80:30180/TCP   98m
database   ClusterIP   10.49.80.6     <none>        2379/TCP       98m
summary    ClusterIP   10.49.96.126   <none>        80/TCP         98m
```

Next, Let's exec into the CentOS pod and verify connectivity to the nginx pod.

```
kubectl exec -ti -n yaobank $(kubectl get pod -l app=customer -n yaobank -o name) bash
	ping 10.48.194.174
	curl -v telnet://10.48.194.174:80
	ping summary
	curl -v telnet://summary:80
	exit
```

You should have the following behaviour:
* ping to the pod ip is successful
* curl to the pod ip is successful
* ping to summary fails
* curl to summary is successful

As we have learned in Lab3, services are  serviced  by kube-proxy which load-balances the service request to backing pods. The service is listening to TCP port 80 so the ping failure is expected.

We have already setup NodePort 30180 for the customer service.
Verify external access from your browser.

```
http://54.187.212.58:30180/

Welcome to YAO Bank
Name: Spike Curtis
Balance: 2389.45
Log Out >>
```
The IP will be different in your lab environment.
In our case, this is the master public ip, then kube proxy takes care of request. 


### 4.1.2. Apply a simple Calico Policy

Let's limit connectivity on the Nginx pods to only allow inbound traffic to port 80 from the CentOS pod.
Examine the manifest before applying it:

``` 
cat 4.1-customer2summary.yaml 

apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: customer2summary
  namespace: yaobank
spec:
  order: 500
  selector: app == "summary"
  ingress:
  - action: Allow
    protocol: TCP
    source:
      selector: app == "customer"
    destination:
      ports:
      - 80
  types:
    - Ingress
```

The policy allows matches the label app=summary which is assigned to summary pods, and allows TCP port 80 traffic from source matching the label app=customer which is assigned to customer pods.
Let's apply our first Calico network policy and examine the effect.

```
calicoctl apply -f 4.1-customer2summary.yaml 
Successfully applied 1 'NetworkPolicy' resource(s)
```

Now, let's repeat the tests we have done in section 4.1.1.
You should have the following behaviour:

* ping to the pod now fails. This is expected since icmp was not allowed in the policy we have applied.
* curl to the pod ip is successful
* ping to summary fails
* curl to summary is successful

Let's cleanup the network policy for now.

```
calicoctl delete -f 4.1-customer2summary.yaml 
Successfully deleted 1 'NetworkPolicy' resource(s)
```
> __Congratulations! You have completed your first Calico network policy lab.__
