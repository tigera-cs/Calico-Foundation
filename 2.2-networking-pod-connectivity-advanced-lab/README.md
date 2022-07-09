## 2.2. Networking:  Pod Connectivity - Advanced Lab

This is the 2nd lab in a series of labs exploring k8s networking. This lab is focused on understanding relevant address ranges and BGP advertisement.

In this lab, you will:

* Examine IP address ranges used by the cluster
* Create an additional Calico IPPool
* Configure Calico BGP Peering to connect with a network outside of the cluster
* Configure a namespace to use externally routable IP addresses

### Before you begin

Please make sure you have completed the previous labs before starting this lab. You should have deployed Calico and the Yaobank sample application in your cluster. 


### Examine IP address ranges used by the cluster


When a Kubernetes cluster is bootstrapped, there are two address ranges that are configured. It is very important to understand these address ranges as they can't be changed once the cluster is created.

* The cluster pod network CIDR is the range of IP addresses Kubernetes is expecting to be assigned to the pods in the cluster.
* The services CIDR is the range of IP addresses that are used for the Cluster IPs of Kubernetes Sevices (the virtual IP that corresponds to each Kubernetes Service).

These are configured at cluster creation time (e.g. as initial kubeadm configuration).

You can find these values using the following command.

```
kubectl cluster-info dump | grep -m 2 -E "service-cluster-ip-range|cluster-cidr"
```

```
kubectl cluster-info dump | grep -m 2 -E "service-cluster-ip-range|cluster-cidr"
                            "--service-cluster-ip-range=10.49.0.0/16",
                            "--cluster-cidr=10.48.0.0/16",
```


### Create an additional Calico IPPool

When Calico is deployed, a defaul IPPool is created in the cluster based on the address family (IPv4-IPv6) enabled in the cluster. This cluster runs only IPv4. As a result, we will only have an IPPool for IPv4. By default, Calico creates a default IPPool for the whole cluster pod network CIDR range. However, this can be customized and a subset of pod network CIDR can be used for the default IPPool.\
Let's find the configured IPPool in this cluster using the following command.

```
calicoctl get ippools
```

```
NAME                  CIDR           SELECTOR   
default-ipv4-ippool   10.48.0.0/24   all() 
```

Please note that you can also get IPPool information using `kubectl` instead of `calicoctl` in the previous command. If you use Openshift, you can replace `calicoctl` with `oc`.

In this cluster, Calico has been configured to allocate IP addresses for pods from the `10.48.0.0/24` CIDR (which is a subset of the `10.48.0.0/16` configured on Kubernetes).

We have the following address ranges configured in this cluster.

| CIDR         |  Purpose                                                  |
|--------------|-----------------------------------------------------------|
| 10.48.0.0/16 | Kubernetes Pod Network (via kubeadm `--pod-network-cidr`) |
| 10.48.0.0/24 | Calico - Initial default IPPool                           |
| 10.49.0.0/16 | Kubernetes Service Network (via kubeadm `--service-cidr`) |



Calico provides a sophisticated and powerful IPAM solution, which enables you to allocate and manage IP addresses for a variety of use cases and requirements.

One of the use cases of Calico IPPool is to distinguish between different ranges of IP addresses that have different routablity scopes. If you are operating at a large scale, then IP addresses are precious resources. You might want to have a range of IPs that is only routable within the cluster, and another range of IPs that is routable across your enterprise. In that case, you can choose which pods get IPs from which range depending on whether workloads from outside of the cluster need direct access to the pods or not.

We'll simulate this use case in this lab by creating a second IPPool to represent the externally routable pool.  (And we've already configured the underlying network to no allow routing of the existing IPPool outside of the cluster.)


We're going to create a new pool for `10.48.2.0/24` that is externally routable.

```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: external-pool
spec:
  cidr: 10.48.2.0/24
  blockSize: 29
  ipipMode: Never
  natOutgoing: true
EOF

```
calicoctl get ippools
```
ubuntu@host1:~/calico/lab-manifests$ calicoctl apply -f 2.2-pool.yaml
Successfully applied 1 'IPPool' resource(s)
ubuntu@host1:~/calico/lab-manifests$ calicoctl get ippools
NAME                  CIDR           SELECTOR   
default-ipv4-ippool   10.48.0.0/24   all()      
external-pool         10.48.2.0/24   all()      
```

We now have:

| CIDR         |  Purpose                                                  |
|--------------|-----------------------------------------------------------|
| 10.48.0.0/16 | Kubernetes Pod Network (via kubeadm `--pod-network-cidr`) |
| 10.48.0.0/24 | Calico - Initial default IP Pool                          |
| 10.48.2.0/24 | Calico - External IP Pool (externally routable)           |
| 10.49.0.0/16 | Kubernetes Service Network (via kubeadm `--service-cidr`) |

### 2.2.3. Configure Calico BGP peering

#### 2.2.3.1. Examine BGP peering status

Switch to worker1:
```
ssh worker1
```

Check the status of Calico on the node:
```bash
sudo calicoctl node status
```
```
Calico process is running.

IPv4 BGP status
+--------------+-------------------+-------+----------+-------------+
| PEER ADDRESS |     PEER TYPE     | STATE |  SINCE   |    INFO     |
+--------------+-------------------+-------+----------+-------------+
| 10.0.0.10    | node-to-node mesh | up    | 19:34:19 | Established |
| 10.0.0.12    | node-to-node mesh | up    | 19:34:19 | Established |
+--------------+-------------------+-------+----------+-------------+

IPv6 BGP status
No IPv6 peers found.
```
This shows that currently Calico is only peering with the other nodes in the cluster and is not peering with any router outside of the cluster.

Exit back to master:
```
exit
```

#### 2.2.3.2. Add a BGP Peer

In this lab we will simulate peering to a router outside of the cluster by peering to host1. We've already set-up host1 to act as a router, and it is ready to accept new BGP peering.

Add the new BGP Peer:
```bash
calicoctl apply -f 2.2-bgp-peer.yaml
```
You should see the following output when you apply the new bgp peer resource. 

```
ubuntu@host1:~$ calicoctl apply -f 2.2-bgp-peer.yaml
Successfully applied 1 'BGPPeer' resource(s)
```

#### 2.2.3.3. Examine the new BGP peering status
Switch to worker1:
```
ssh worker1
```

Check the status of Calico on the node:
```bash
sudo calicoctl node status
```
```
ubuntu@worker1:~$ sudo calicoctl node status
Calico process is running.

IPv4 BGP status
+--------------+-------------------+-------+------------+-------------+
| PEER ADDRESS |     PEER TYPE     | STATE |   SINCE    |    INFO     |
+--------------+-------------------+-------+------------+-------------+
| 10.0.0.10    | node-to-node mesh | up    | 2019-11-13 | Established |
| 10.0.0.12    | node-to-node mesh | up    | 2019-11-13 | Established |
| 10.0.0.20    | global            | up    | 04:28:42   | Established |
+--------------+-------------------+-------+------------+-------------+

IPv6 BGP status
No IPv6 peers found.
```

The output shows that Calico is now peered with host1 (`10.0.0.20`). This means Calico can share routes to and learn routes from host1.

In a real-world on-prem deployment you would typically configure Calico nodes within a rack to peer with the ToRs (Top of Rack) routers, and the ToRs are then connected to the rest of the enterprise or data center network. In this way pods, if desired, pods can be reached from anywhere in then network. You could even go as far as giving some pods public IP address and have them addressable from the internet if you wanted to.

We're done with adding the peers, so exit from worker1 to return back to master:
```
exit
```

### 2.2.4. Configure a namespace to use externally routable IP addresses

Calico supports annotations on both namespaces and pods that can be used to control which IP Pool (or even which IP address) a pod will receive when it is created.  In this example we're going to create a namespace to host externally routable Pods.

#### 2.2.4.1. Create the namespace

Examine the namespaces we're about to create:
```
more 2.2-namespace.yaml
```
Notice the annotation that will determine which IP Pool pods in the namespace will use.

Apply the namespace:
```bash
kubectl apply -f 2.2-namespace.yaml
```
```
ubuntu@host1:~$ kubectl apply -f 2.2-namespace.yaml
namespace/external-ns created
```

#### 2.2.4.2. Deploy an nginx pod
Now deploy a NGINX example pod in the `external-ns` namespace, along with a simple network policy that allows ingress on port 80.
```
kubectl apply -f 2.2-nginx.yaml
```
```
ubuntu@host1:~/calico/lab-manifests$ kubectl apply -f 2.2-nginx.yaml
deployment.apps/nginx created
networkpolicy.networking.k8s.io/nginx created
```

#### 2.2.4.3. Access the nginx pod from outside the cluster

Let's see what IP address was assigned:
```
kubectl get pods -n external-ns -o wide
```
```
ubuntu@host1:~/calico/lab-manifests$ kubectl get pods -n external-ns -o wide
NAME                     READY   STATUS    RESTARTS   AGE     IP            NODE      NOMINATED NODE   READINESS GATES
nginx-7bb7cd8db5-zqzks   1/1     Running   0          5m44s   10.48.2.232   worker1   <none>           <none>
```

The output shows that the nginx pod has an IP address from the externally routable IP Pool.

Try to connect to it from host1:
```
curl 10.48.2.232
```

This should have succeeded, showing that the nginx pod is directly routable on the broader network.

If you would like to see IP allocation stats from Calico-IPAM, run the following command.

```
calicoctl ipam show
```

> __You have completed Lab2.2 and you should have by now a strong understanding of k8s networking__
