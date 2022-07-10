## 4.3. Network Policy - Advanced Lab

This is the 3rd lab in a series of labs exploring network policies.

In this lab you will:

* Create Egress Lockdown policy as a Security Admin for the cluster
* Grant selective Internet access
* Protect the Host


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

### Protect the Host

Thus far, we've created policies that protect pods in Kubernetes. However, Calico Policy can also be used to protect the host interfaces in any standalone Linux node (such as a baremetal node, cloud instance or virtual machine) outside the cluster. Furthermore, it can also be used to protect the Kubernetes nodes themselves.

The protection of Kubernetes nodes themselves highlights some of the unique capabilities of Calico. We need to account for various control plane services (such as the apiserver, kubelet, controller-manager, etcd, and others) and allow the traffic. In addition, one needs to also account for certain pods that might be running with host networking (i.e., using the host IP address for the pod) or using hostports. To add an additional layer of challenge, there are also various services (such as Kubernetes NodePorts) that can take traffic coming to reserved port ranges in the host (such as 30000-32767) and NAT it prior to forwarding to a local destination (and perhaps even SNAT traffic prior to redirecting it to a different worker node). 

Lets explore these more advanced scenarios.
Lets start by seeing how the default cluster deployment using kubeadm have left some control plane services exposed to the world.
Identifiy where etcd is running.

```
kubectl get pod -n kube-system -l component=etcd -o wide
```

```
NAME                                           READY   STATUS    RESTARTS   AGE   IP          NODE                                      NOMINATED NODE   READINESS GATES
etcd-ip-10-0-1-20.eu-west-1.compute.internal   1/1     Running   0          11h   10.0.1.20   ip-10-0-1-20.eu-west-1.compute.internal   <none>           <none>
```

Now, let's try to access it from our bastion node.

```
curl -v 10.0.1.20:2379
```

```
*   Trying 10.0.1.20:2379...
* TCP_NODELAY set
* Connected to 10.0.1.20 (10.0.1.20) port 2379 (#0)
> GET / HTTP/1.1
> Host: 10.0.1.20:2379
> User-Agent: curl/7.68.0
> Accept: */*
> 
* Empty reply from server
* Connection #0 to host 10.0.1.20 left intact
curl: (52) Empty reply from server
```

This should succeed because the Kubernetes cluster's ETCD store is left exposed for attacks along with the rest of the control plane. This could lead to a compromise if not handled properly.


Lets create some host endpoint policies for the kubernetes master and worker nodes.
Examine the policy first before applying it.

```
more 4.3-global-host-policy.yaml


apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: k8s-master2master-allowed-ports
spec:
  selector: k8s-master == "true"
  order: 300
  ingress:
  - action: Allow
    protocol: TCP
    source:
      selector: k8s-master == "true"
    destination:
      ports: ["2379:2380", 4001, "10250:10256", 9099, 6443 ]
  egress:
  - action: Allow

---
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: k8s-outside2master-allowed-ports
spec:
  selector: k8s-master == "true"
  order: 350
  ingress:
  - action: Allow
    protocol: TCP
    destination:
      ports: [10250, 6443]
  - action: Allow
    protocol: UDP
    destination:
      ports: [53]
  egress:
  - action: Allow


---

apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: k8s-outside2worker-allowed-ports
spec:
  selector: k8s-worker == "true"
  order: 400
  ingress:
  - action: Allow
    protocol: TCP
    destination:
      ports: [10250, 10256 ]
  egress:
  - action: Allow
---


apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: block-k8s-nodeports
spec:
  selector: k8s-worker == "true"
  order: 450
  applyOnForward: true
  preDNAT: true
  ingress:
  - action: Deny
    protocol: TCP
    destination:
      ports: ["30000:32767"]
  - action: Deny
    protocol: UDP
    destination:
      ports: ["30000:32767"]

```

```
calicoctl apply -f 4.3-global-host-policy.yaml
```

We have created the policy that locks down the control plane such that the worker nodes only have kubelet exposed, and the master nodes only have important services (like Etcd) accessible only from other master nodes.

#### 4.3.3.3. Create Host Endpoints

Before creating the Host Endpoints in k8s, Calico cannot enforce policies on hosts. Let's now create the Host Endpoints themselves, allowing Calico to start policy enforcement on the nodes ethernet interface. While we're at it, lets also lockdown nodePorts.

Eaxmine the policy first before applying it.

```
more 4.3-host-endpoint.yaml

apiVersion: projectcalico.org/v3
kind: HostEndpoint
metadata:
  name: master1
  labels:
    k8s-master: true
    k8s-worker: true
spec:
  interfaceName: ens160
  node: master1
  expectedIPs: ["10.0.0.10"]
---
apiVersion: projectcalico.org/v3
kind: HostEndpoint
metadata:
  name: worker1
  labels:
    k8s-worker: true
spec:
  interfaceName: ens160
  node: worker1
  expectedIPs: ["10.0.0.11"]
---
apiVersion: projectcalico.org/v3
kind: HostEndpoint
metadata:
  name: worker2
  labels:
    k8s-worker: true
spec:
  interfaceName: ens160
  node: worker2
  expectedIPs: ["10.0.0.12"]

```


```
calicoctl apply -f 4.3-host-endpoint.yaml
```


#### 4.3.3.4. Now lets attempt to attack etcd from the standalone host. Run the curl again from the standalone host (host1):

```
curl -v  -m 5 10.0.0.10:2379
```

This time the curl should fail, and timeout after 5 seconds. 
We have successfully locked down the Kubernetes control plane to only be accessible from relevant nodes.



> __Congratulations! You have completed your Calico advanced policy lab.__
