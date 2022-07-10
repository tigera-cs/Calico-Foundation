## 4.3. Network Policy - Advanced Lab

This is the 3rd lab in a series of labs exploring network policies.

In this lab you will:

* Create Egress Lockdown policy as a Security Admin for the cluster
* Grant selective Internet access
* 


### Before you begin

This lab builds on top of the previous labs. Please make sure you have completed the previous labs before starting this lab.


### Create Egress Lockdown policy as a Security Admin for the cluster

This lab guides you through the process of deploying a egress lockdown policy in our cluster.
In the previous lab, we applied a policy that allows wide open egress access to customer and summary pods. Best-practices call for a restrictive policy that allows minimal access and denies everything else.

Let's first start with verifying connectivity with the configuration applied in the previous lab. Confirm that the customer pod is able to initiate connections to the Internet.

Exec into the customer pod.

```
CUSTOMER_POD=$(kubectl get pod -l app=customer -n yaobank -o jsonpath='{.items[0].metadata.name}')
echo $CUSTOMER_POD
kubectl exec -ti $CUSTOMER_POD -n yaobank -c customer bash

```

```
ping -c 3 8.8.8.8
```

```
curl -I www.google.com
```

```
exit
```

This succeeds since the policy in place allows full internet access.

Let's now create a Calico GlobalNetworkPolicy to restrict egress access to the Internet to only pods that have the ServiceAccount that is labeled  "internet-egress = allowed".


Examine the policy before applying it. While Kubernetes network policies only have Allow rules, Calico network policies also support Deny rules. As this policy has Deny rules in it, it is important that we set its precedence higher than the K8s policy Allow rules. To do this, we specify `order`  value of 600 in this policy, which gives it higher precedence than the k8s policy (which does not have the concept of policy precedence, and is assigned a fixed order value of 1000 by Calico). 

```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: egress-lockdown
spec:
  order: 600
  selector: ''
  types:
  - Egress
  egress:
    - action: Allow
      source:
        serviceAccounts:
          selector: internet-egress == "allowed"
      destination: {}
    - action: Deny
      source: {}
      destination:
        notNets:
          - 10.48.0.0/16
          - 10.49.0.0/16
          - 10.50.0.0/24
          - 10.0.0.0/24
EOF

```
Notice the notNets destination parameter that excludes known cluster networks from the deny rule. 

Verify Internet access again. Exe into the customer pod.

```
CUSTOMER_POD=$(kubectl get pod -l app=customer -n yaobank -o jsonpath='{.items[0].metadata.name}')
echo $CUSTOMER_POD
kubectl exec -ti $CUSTOMER_POD -n yaobank -c customer bash

```

```
ping -c 3 8.8.8.8
```

```
curl -I www.google.com
```

```
exit
```

These commands should fail. Pods are now restricted to only accessing other pods and nodes within the cluster. You may need to terminate the command with ctrl+c and exit back to your node.

```
exit
```

### Grant selective Internet access

Now let's take the case where there is a legitimate reason to allow connections from the Customer pod to the Internet. As we used a Service Account label selector in our egress policy rules, we can enable this by adding the appropriate label to the pod's Service Account.


```
kubectl label serviceaccount -n yaobank customer internet-egress=allowed
```

Verify that the customer pod can now access the Internet.

```
CUSTOMER_POD=$(kubectl get pod -l app=customer -n yaobank -o jsonpath='{.items[0].metadata.name}')
echo $CUSTOMER_POD
kubectl exec -ti $CUSTOMER_POD -n yaobank -c customer bash

```

```
ping -c 3 8.8.8.8
```

```
curl -I www.google.com
```

```
exit
```

Now you should find that the customer pod is allowed Internet access, but other pods (like Summary and Database) are not.


There are many ways for dividing responsibilities across teams using Kubernetes RBAC.

Let's take the following case:

* The SecOps team is responsible for creating Namespaces and Services accounts for dev teams. Kubernetes RBAC is setup so that only they can do this.
* Dev teams are given Kubernetes RBAC permissions to create pods in their Namespaces and they can use but not modify any Service Account in their Namespaces.

In this scenario, the SecOps team can control which teams should be allowed to have pods that access the Internet.  If a dev team is allowed to have pods that access the Internet then the dev team can choose which pods access the Internet by using the appropriate Service Account. 

This is just one way of dividing responsibilities across teams.  Pods, Namespaces, and Service Accounts all have separate Kubernetes RBAC controls and they can all be used to select workloads in Calico network policies.





> __Congratulations! You have completed your Calico advanced policy lab.__
