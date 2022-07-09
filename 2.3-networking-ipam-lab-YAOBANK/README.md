## 2.3. Networking: Calico-IPAM Lab

This is the 3rd lab in a series of labs exploring k8s networking. It explores k8s ip adress management via Calico IPAM.

In this lab, you will:
* Check existing IPPools and create new IPPools 
* Update the yaobank deployments with the new IPPools
* Verify the host routing

### Check existing IPPools and create new IPPools 

Check the IPPools that exist in the cluster. You should see two IPPools, one (default-ipv4-ippool) was created at the cluster creation time using the Installation resource and the other (external-pool) was created in the previous lab as part of checking pod's external connectivity exercise.

```
kubectl get ippools.projectcalico.org
```
You should receive an output similar to the following.
```
NAME                  CREATED AT
default-ipv4-ippool   2022-07-09T17:44:37Z
external-pool         2022-07-09T20:02:25Z
```
Let's check the details of the `default-ipv4-ippool` and get familiar with some configuration parameters in the IPPool.

```
kubectl get ippool default-ipv4-ippool -o yaml
```

```
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  creationTimestamp: "2022-07-09T17:44:37Z"
  name: default-ipv4-ippool
  resourceVersion: "7202"
  uid: 49ecd163-1a83-4566-872a-fb0390102724
spec:
  allowedUses:
  - Workload
  - Tunnel
  blockSize: 26
  cidr: 10.48.0.0/24
  ipipMode: Never
  natOutgoing: true
  nodeSelector: all()
  vxlanMode: Never
```

We have extracted the relevant information here. You can see from the output that the default IPPool range is 10.48.0.0/24, which is actually the Calico Initial default IP Pool range of our k8s cluster.
Note the relevant information in the manifest:

* allowedUses: specifies if this IPPool can be used for tunnel interfaces, workload interfaces, or both.
* blockSize: used by Calico IPAM to efficiently assign IPAM Blocks to node and advertise the between different nodes.
* cidr: specifies the IP range to be used for this IPPool.
* ipipMode/vxlanMode: to enable or disable ipip and vxlan overlay. options are never, always and crosssubnet.
* natOutgoing: specifies if SNAT should happen when pods try to connect to destination outside the cluster. `natOutgoing` must be set to `true` when using overlay networking mode for external connectivity.
* nodeSelector: selects the nodes that Calico IPAM should assign addresses from this pool to.


Let's create a new IPPool by applying the following manifest.

```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: pool2-ipv4-ippool
spec:
  blockSize: 26
  cidr: 10.48.128.0/24
  ipipMode: Never
  natOutgoing: true
  nodeSelector: all()
EOF

```
You should receive an output similar to the following.

```
calicoctl apply -f 2.3-ippools.yaml 
Successfully applied 2 'IPPool' resource(s)
```

```
calicoctl get ippools
NAME                CIDR             SELECTOR   
pool1-ipv4-ippool   10.48.0.0/17     all()      
pool2-ipv4-ippool   10.48.128.0/17   all()     
```

We have now the  so that we can test ipam address assignment

### 2.3.2. Update the yaobank deployments with the new IP Pools

Now let's update the yao

 the pools that yaobank manifest we have deployed in Lab1, adding annotation to explicitly define the ip pool for each deployment. Examine the manifest 2.3-yaobank-ipam.yaml before deploying, specifically the pod the ip pool  annotations.

```
cat 2.3-yaobank-ipam.yaml

```

```
    metadata:
      annotations:
        "cni.projectcalico.org/ipv4pools": "[\"pool2-ipv4-ippool\"]"

```

The annotation explicitly assigns ip pool1 to customer deployment and pool2 to summary and database deployments. Let's apply the manifest and examine the outcome.

```
kubectl apply -f 2.3-yaobank-ipam.yaml 

namespace/yaobank unchanged
service/database unchanged
serviceaccount/database unchanged
deployment.extensions/database configured
service/summary unchanged
serviceaccount/summary unchanged
deployment.extensions/summary configured
service/customer unchanged
serviceaccount/customer unchanged
deployment.extensions/customer configured
```

The deployment pods already have ip addresses assigned so we will need to delete the old pods, which will trigger kubernetes scheduler to new pod in conformance with the deployment manifest (the intent) and accordingly apply the ip pool binding.

```
kubectl delete -n yaobank pod $(kubectl get pod -l app=customer -n yaobank -o jsonpath='{.items[0].metadata.name}')
kubectl delete -n yaobank pod $(kubectl get pod -l app=database -n yaobank -o jsonpath='{.items[0].metadata.name}')
kubectl delete -n yaobank pod $(kubectl get pod -l app=summary -n yaobank -o jsonpath='{.items[0].metadata.name}')
kubectl delete -n yaobank pod $(kubectl get pod -l app=summary -n yaobank -o jsonpath='{.items[1].metadata.name}')
```



Next, examine the Pods ip address assignment.

```
kubectl get pod -n yaobank -o wide

NAME                        READY   STATUS    RESTARTS   AGE     IP              NODE           NOMINATED NODE   READINESS GATES
customer-84c7855fd4-55r26   1/1     Running   0          14m     10.48.110.14    ip-10-0-0-11   <none>           <none>
database-56fb9496bb-mdch5   1/1     Running   0          13m     10.48.194.175   ip-10-0-0-12   <none>           <none>
summary-7f89fbcc7c-tsqjz    1/1     Running   0          24m     10.48.194.174   ip-10-0-0-12   <none>           <none>
summary-7f89fbcc7c-vl9px    1/1     Running   0          2m56s   10.48.177.96    ip-10-0-0-10   <none>           <none>

```
You can see that Pod ip address assignment is aligned with the intend defined in the updated manifest, assigning pods of a deployment to the correct ip pool.  Calico IPAM provides the flexibility as well of assigning ippools to namespaces or even in alignment with your topology to specific nodes or racks.

### 2.3.3. Verify host routing

Let's check host routing to understand the effect of the subnetting and ip address assignment we have done to routing.

From the output in section 2.3.2, you can see that one customer Pod is running on worker1 and the remaining pods are running on the master node and worker 2. Let's examine the routing table of the master node.

```
ip route

10.48.110.14 dev calif0d1818d01e scope link 
blackhole 10.48.110.0/26 proto bird 
10.48.177.64/26 via 10.0.0.10 dev eth0 proto bird 
10.48.194.128/26 via 10.0.0.12 dev eth0 proto bird 
```

Examine the output of the routing table that is relevant to our deployment:
* specific routes point to the veth interfaces connecting to local pods
* blackhole route is created for the ip block local to the host (saying do route traffic for the local/26 block to any other node)
* routes to the pod on worker2 and master are learned via BPG and a /26 block advertisement from the nodes

> __Congratulations! You have completed you Calico IPAM lab.__ 
