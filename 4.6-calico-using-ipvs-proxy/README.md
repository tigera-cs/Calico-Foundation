
# Install Calico in IPVS mode


Calico has support for kube-proxy’s ipvs proxy mode. Calico ipvs support is activated automatically if Calico detects that kube-proxy is running in that mode.

ipvs mode provides greater scale and performance vs iptables mode. 

## Requirements

1. A cluster running Kubernetes v1.11+
2. Load the below required kernel modules and install `ipvsadm` and `ipset` on all the nodes. (SSH into each node and run the below commands)

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

```
I0710 22:26:27.584923       1 server_others.go:274] Using ipvs Proxier.
I0710 22:26:37.773549       1 server_others.go:274] Using ipvs Proxier.
I0710 22:26:45.418173       1 server_others.go:274] Using ipvs Proxier.
```

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


If you try connecting to our `service-nginx` created in this lab from any of the worker node, the connection should randonmly go through and fail due to our previously implemented network policy blocking the traffic. The connections only go through when kube-proxy forwards the traffic to an endpoint local to the node. This is because nodes have privileged access to the pods running on them.

Try connecting `service-nginx` from worker1  for few times and notice the behavior.

```
ssh worker1
```

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

Open two terminal sessions and SSH into worker1. Note that both of the following commands need to run from the same host.


Run the following command to analyze the packet flow per second in IPVS mode. Initially, all the traffic counters need to be zero for `service-nginx`.

```
watch sudo ipvsadm -L -n --rate

```

Run the following script to generate traffic for the `service-nginx` service and check the output stats in other terminal again. This time you should see the traffic counters increasing. Please make sure to replace the service IP in the following command.

```
for i in {1..30}; do  curl <service-ip>:80 ; done
```

You should see the traffic getting distributed among the pods using `rr algorithm`' Following is a sample output.

```
Every 2.0s: sudo ipvsadm -L -n --rate                                                                                                                                                                                                                                                                   ip-10-0-1-30.eu-west-1.compute.internal: Sun Jul 10 18:11:16 2022

IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port                 CPS    InPPS   OutPPS    InBPS   OutBPS
  -> RemoteAddress:Port
TCP  172.17.0.1:30180                    0        0        0        0        0
  -> 10.48.0.14:80                       0        0        0        0        0
TCP  10.0.1.30:30180                     0        0        0        0        0
  -> 10.48.0.14:80                       0        0        0        0        0
TCP  10.49.0.1:443                       0        0        0        0        0
  -> 10.0.1.20:6443                      0        0        0        0        0
TCP  10.49.0.10:53                       0        0        0        0        0
  -> 10.48.0.1:53                        0        0        0        0        0
  -> 10.48.0.193:53                      0        0        0        0        0
TCP  10.49.0.10:9153                     0        0        0        0        0
  -> 10.48.0.1:9153                      0        0        0        0        0
  -> 10.48.0.193:9153                    0        0        0        0        0
TCP  10.49.23.129:80                     0        0        0        0        0
  -> 10.48.0.199:80                      0        0        0        0        0
TCP  10.49.72.138:443                    0        0        0        0        0
  -> 10.0.1.30:8443                      0        0        0        0        0
  -> 10.0.1.31:8443                      0        0        0        0        0
TCP  10.49.97.116:9094                   0        0        0        0        0
  -> 10.48.0.192:9094                    0        0        0        0        0
TCP  10.49.119.221:2379                  0        0        0        0        0
  -> 10.48.0.12:2379                     0        0        0        0        0
TCP  10.49.120.28:80                     1        6        4      399      995
  -> 10.48.0.18:80                       0        2        1      133      332
  -> 10.48.0.201:80                      0        2        1      133      332
  -> 10.48.0.202:80                      0        2        1      133      332
TCP  10.49.138.47:443                    0        0        0        0        0
  -> 10.48.0.3:5443                      0        0        0        0        0
  -> 10.48.0.194:5443                    0        0        0        0        0
TCP  10.49.149.29:5473                   0        0        0        0        0
  -> 10.0.1.30:5473                      0        0        0        0        0
  -> 10.0.1.31:5473                      0        0        0        0        0
TCP  10.49.160.175:80                    0        0        0        0        0
  -> 10.48.0.14:80                       0        0        0        0        0
TCP  10.49.191.55:80                     0        0        0        0        0
  -> 10.48.0.16:80                       0        0        0        0        0
  -> 10.48.0.17:80                       0        0        0        0        0
  -> 10.48.0.200:80                      0        0        0        0        0
TCP  10.49.202.152:80                    0        0        0        0        0
  -> 10.48.0.13:80                       0        0        0        0        0
  -> 10.48.0.198:80                      0        0        0        0        0
TCP  127.0.0.1:30180                     0        0        0        0        0
  -> 10.48.0.14:80                       0        0        0        0        0
UDP  10.49.0.10:53                       0        0        0        0        0
  -> 10.48.0.1:53                        0        0        0        0        0
  -> 10.48.0.193:53                      0        0        0        0        0
```


