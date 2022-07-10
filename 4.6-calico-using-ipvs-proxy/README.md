
# Install Calico in IPVS mode


Calico has support for kube-proxy’s ipvs proxy mode. Calico ipvs support is activated automatically if Calico detects that kube-proxy is running in that mode.

ipvs mode provides greater scale and performance vs iptables mode. 

## Requirements

1. A cluster running Kubernetes v1.11+
2. Load the below required kernel modules and install `ipvsadm` and `ipset` on all the cluster nodes. (SSH into each cluster node and run the below commands)

```
sudo apt install -y ipvsadm ipset
```
Load the kernel modules.

```
sudo modprobe ip_vs 
sudo modprobe ip_vs_rr
sudo modprobe ip_vs_wrr 
sudo modprobe ip_vs_sh
sudo modprobe nf_conntrack
sudo sysctl --system
sudo sysctl -p
```

Check that the kernel modules are loaded.

```
lsmod | grep -e ip_vs -e nf_conntrack
cut -f1 -d " " /proc/modules | grep -e ip_vs -e nf_conntrack
```


## Steps to enable IPVS mode 

1. Change the configMap of kube-proxy, modify "mode" from "" to "ipvs"

```
kubectl -n kube-system edit cm kube-proxy
```

2. Delete all the active proxy pods

```
for i in $(kubectl get pods -n kube-system -o name | grep kube-proxy) ; do kubectl delete $i -n kube-system ; done
```

3. Check the logs of new kube-proxy pods

```
for i in $(kubectl get pods -n kube-system -o name | grep kube-proxy) ; do kubectl logs $i -n kube-system | grep "Using ipvs Proxier" ; done
```

If you are able to find the mentioned String in the logs, IPVS mode is being used by the cluster. You can also check the detailed logs for the IPVS mode.

## Verify and Debug IPVS

Users can use ipvsadm tool to check whether kube-proxy are maintaining IPVS rules correctly. This needs to be done from any of the cluster nodes and not the bastion node. WeIn this example, we will use the kubernetes APIserver. You can follow the below procedure to check on the IPVS loadbalancing rules for other services in the cluster.

```
ssh worker1
```

```
kubectl get svc
``` 

```
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.49.0.1    <none>        443/TCP   24h
```

As the API server has a single endpoint because our cluster only has one master node, we can grep a single line below the Cluster IP to check the IPVS proxy rules for it.

Following are the IPVS proxy rules for above services

```
sudo ipvsadm -ln | grep -A1 10.49.0.1:443
```

```
TCP  10.49.0.1:443 rr
  -> 10.0.1.20:6443               Masq    1      0          0    
```


## Why kube-proxy can't start IPVS mode
Use the following check list to help you troubleshoot IPVS related issues.

1. Specify `mode=ipvs` 

Check whether the kube-proxy mode has been set to ipvs in the `kube-proxy` configmap.

3. Install required kernel modules and packages

Check whether the IPVS required kernel modules have been compiled into the kernel and packages installed. (see Requirements)


## Demo

Considering that you have the cluster running in `ipvs` mode and Calico is now configured, lets us create a `nginx-deployment` and a `service` and observe how `ipvs` loadbalancing works.


```
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: service-nginx
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
EOF

```
Examine the ClusterIP of `service-nginx` service.

```
kubectl get svc
```

```
NAME            TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
kubernetes      ClusterIP   10.49.0.1      <none>        443/TCP   24h
service-nginx   ClusterIP   10.49.120.28   <none>        80/TCP    52s
```

Now let's list the ipvs table and check how are service maps to the pods created using deployment. (This command needs to run from one of the worker nodes).

```
ssh worker1
```

```
sudo ipvsadm -l | grep -A3 $(kubectl get svc service-nginx --no-headers | awk {'print $3'})
```

```
TCP  ip-10-49-120-28.eu-west-1.co rr
  -> ip-10-48-0-18.eu-west-1.comp Masq    1      0          0         
  -> ip-10-48-0-201.eu-west-1.com Masq    1      0          0         
  -> ip-10-48-0-202.eu-west-1.com Masq    1      0          0 
```
In the above output, `ip-10-99-170-70.us-west-2.co` is the service and just below the service you can see the list of pods/endpoints. `rr` means the loadbalancing used is `round-robin`.

In our previous lab, we advertised the Kubernetes service CIDR to the bastion node. Check the bastion node routing table. You should see routes `10.49.0.0/16` to the Kubernetes service CIDR.

```
ip route
```

```
default via 10.0.1.1 dev ens5 proto dhcp src 10.0.1.10 metric 100 
10.0.1.0/24 dev ens5 proto kernel scope link src 10.0.1.10 
10.0.1.1 dev ens5 proto dhcp scope link src 10.0.1.10 metric 100 
10.48.2.216/29 via 10.0.1.31 dev ens5 proto bird 
10.49.0.0/16 proto bird 
        nexthop via 10.0.1.20 dev ens5 weight 1 
        nexthop via 10.0.1.30 dev ens5 weight 1 
        nexthop via 10.0.1.31 dev ens5 weight 1 
10.50.0.0/24 proto bird 
        nexthop via 10.0.1.20 dev ens5 weight 1 
        nexthop via 10.0.1.30 dev ens5 weight 1 
        nexthop via 10.0.1.31 dev ens5 weight 1 
```

However, if you try connecting to our `service-nginx` created in this lab, the connectivity should fail due to our previously implemented network policy blocking the traffic. 
Try connecting `service-nginx` from the bastion node.

```
curl 10.49.120.28
```

Let's implement a network policy that allows this communication. Note this policy allows ingress traffic from any source and egress traffic to any destination.

```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: nginx-server-allow-all
  namespace: default
spec:
  selector: app == "nginx"
  ingress:
    - action: Allow
      protocol: TCP
      source: {}
      destination:
        ports:
          - '80'
  egress:
    - action: Allow
      source: {}
      destination: {}
  types:
    - Ingress
    - Egress
EOF

```


If you are on the same host i.e. Master you can run the following script to generate traffic for the service and check the output stats in other tab by doing the following.

```
for i in {1..10}; do  curl <service-ip>:80 ; done

In the next tab analyze the packet flow per second using

watch sudo ipvsadm -L -n --rate

```
Here you will see the traffic getting distributed among the pods using `rr algorithm`
