## Networking: Pod Connectivity - Basic Lab

This lab is the first of a series of labs exploring orchestration (k8s, ocp) networking concepts. This lab focuses on basic networking from the POD and Host perspectives.
In this lab, you will:
a. Examine what the network looks like from the perspecitve of a pod (the pod network namespace)
b. Examine what the network looks like from the perspecitve of the host (the host network namespace)

### Before you begin

Make sure you have access to your cluster and Calico Enterprise is installed, up and running.

### Examine pod network namespace

We'll start by examining what the network looks like from the pod's point of view. Each pod get's its own Linux network namespace, which you can think of as giving it an isolated copy of the Linux networking stack.

#### Find the name and location of the frontend pod
From k8s master node, get the details of the frontend pod using the following command.
```
kubectl get pods -n development -l app=frontend -o wide
```
```
NAME                        READY   STATUS    RESTARTS   AGE     IP               NODE                                         NOMINATED NODE   READINESS GATES
frontend-656649f4bb-j5p4l   1/1     Running   0          5h24m   10.129.102.142   ip-10-0-138-141.us-west-2.compute.internal   <none>           <none>

```

#### Exec into the frontend pod
Use kubectl to exec into the pod so we can check the pod networking details.
```
kubectl exec -ti -n development $(kubectl get pods -n development -l app=frontend -o name) bash
apt install iproute2 -y
```

#### Examine the pod's networking
First we will use `ip addr` to list the addresses and associated network interfaces that the pod sees.
```
ip addr
```

```
root@frontend-656649f4bb-j5p4l:/app# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: tunl0@NONE: <NOARP> mtu 1480 qdisc noop state DOWN group default qlen 1000
    link/ipip 0.0.0.0 brd 0.0.0.0
4: eth0@if20: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1410 qdisc noqueue state UP group default
    link/ether be:d3:43:9e:ec:bb brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.129.102.142/32 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::bcd3:43ff:fe9e:ecbb/64 scope link
       valid_lft forever preferred_lft forever
```

The key things to note in this output are:
* There is a `lo` loopback interface with an IP address of `127.0.0.1`. This is the standard loopback interface that every network namespace has by default. You can think of it as `localhost` for the pod itself.
* There is an `eth0` interface which has the pods actual IP address, `10.129.102.142`. Notice this matches the IP address that `kubectl get pods` returned earlier.

Next let's look more closely at the interfaces using `ip link`.  We will use the `-c` option, which colours the output to make it easier to read.

```
ip -c link
```
```
root@frontend-656649f4bb-j5p4l:/app# ip -c link
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: tunl0@NONE: <NOARP> mtu 1480 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ipip 0.0.0.0 brd 0.0.0.0
4: eth0@if20: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1410 qdisc noqueue state UP mode DEFAULT group default
    link/ether be:d3:43:9e:ec:bb brd ff:ff:ff:ff:ff:ff link-netnsid 0
```

Look at the `eth0` part of the output. The key things to note are:
* The `eth0` interface is interface number 4 in the pod's network namespace.
* `eth0` is a link to the host network namespace (indicated by `link-netnsid 0`). i.e. It is the pod's side of the veth pair (virtual ethernet pair) that connects the pod to the host's networking.
* The `@if20` at the end of the interface name is the interface number of the other end of the veth pair within the host's network namespaces. In this example, interface number 20.  Remember this for later. We will take look at the other end of the veth pair shortly.

Finally, let's look at the routes the pod sees.

```
ip route
```
```
root@frontend-656649f4bb-j5p4l:/app# ip route
default via 169.254.1.1 dev eth0
169.254.1.1 dev eth0 scope link
```
This shows that the pod's default route is out over the `eth0` interface. i.e. Anytime it wants to send traffic to anywhere other than itself, it will send the traffic over `eth0`.

#### Exit from the frontend pod
We've finished our tour of the pod's view of the network, so we'll exit out of the pod.
```
exit
```

#### Note - In case of Opesnshift Deployments we do not have access to the actual host, hence the below details might not match exactly and are for demonstration purpose. Below details can be considered as reference to Host Networking.

### Examine the host's network namespace

#### Examine interfaces
Now we're on the node hosting the frontend pod we'll take a look to examine the other end of the veth pair. In our example output earlier, the `@if20` indicated it should be interface number 20 in the host network namespace. (Your interface numbers may be different, but you should be able to follow along the same logic.)
```
ip -c link
```
```
ubuntu@worker1:~$ ip -c link
17: cali282de2964bf@if4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
    link/ether ee:ee:ee:ee:ee:ee brd ff:ff:ff:ff:ff:ff link-netnsid 0
18: cali4b8cf63cac1@if4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
    link/ether ee:ee:ee:ee:ee:ee brd ff:ff:ff:ff:ff:ff link-netnsid 1
19: cali2b0ff6bbf7d@if4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
    link/ether ee:ee:ee:ee:ee:ee brd ff:ff:ff:ff:ff:ff link-netnsid 2
20: calie965c96dc90@if4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
    link/ether ee:ee:ee:ee:ee:ee brd ff:ff:ff:ff:ff:ff link-netnsid 3
```

Looking at interface number 20 in this example we see `calie965c96dc90` which links to `@if3` in network namespace ID 4 (the frontend pod's network namespace).  You may recall that interface 4 in the pod's network namespace was `eth0`, so this looks exactly as expected for the veth pair that connects the frontend pod to the host network namespace.

You can also see the host end of the veth pairs to other pods running on this node, all beginning with `cali`.

#### Examine routes
First let's remind ourselves of the `frontend` pod's IP address:
```
kubectl get pods -n development -l app=frontend -o wide
````

Now lets look at the routes on the host.

If your are using a openshift cluster run the following set of commands to get nodes, open a debug session to that node, install necessary pacakges and inspect host networking

```
oc get nodes -o wide

oc debug node/<node-name>

After entering the root prompt

yum install iproute -y

ip route
```
```
sh-4.2# ip route
10.129.63.19 dev cali282de2964bf scope link
blackhole 10.129.x.y/26 proto bird
10.129.63.20 dev cali4b8cf63cac1 scope link
10.131.234.23 dev cali2b0ff6bbf7d scope link
10.129.102.142 dev calie965c96dc90 scope link
10.129.x.x/26 via 10.0.138.141 dev ens160 proto bird
```

In this example output, we can see the route to the frontend pod's IP (`10.129.102.142`) is via the `calie965c96dc90` interface, the host end of the veth pair for the frontend pod. You can see similar routes for each of the IPs of the other pods hosted on this node. It's these routes that tell Linux where to send traffic that is destined to a local pod on the node.

We can also see routes labelled `proto bird`. These are routes to pods on other nodes that Calico has learned over BGP.

To understand these better, consider this route in the example output above `10.129.x.x/26 via 10.0.165.129 dev ens160 proto bird`.  It indicates pods with IP addresses falling within the `10.48.x.x/26` CIDR can be reached via `10.0.165.129` through the `ens160` network interface (the host's main interface to the rest of the network). You should see similar routes in your output for each node.

Calico uses route aggregation to reduce the number of routes when possible. (e.g. `/26` in this example). The `/26` corresponds to the default block size that Calico IPAM (IP Address Management) allocates on demand as nodes need pod IP addresses. (If desired, the block size can be configured in Calico IPAM settings.)

You can also see the `blackhole 10.129.x.y/26 proto bird` route. The `10.129.x.y/26` corresponds to the block of IPs that Calico IPAM allocated on demand for this node. This is the block from which each of the local pods got their IP addresses. The blackhole route tells Linux that if it can't find a more specific route for an individual IP in that block then it should discard the packet (rather than sending it out the default route to the network). You will only see traffic that hits this rule if something is trying to send traffic to a pod IP that doesn't exist, for example sending traffic to a recently deleted pod.

If Calico IPAM runs out of blocks to allocate to nodes, then it will use unused IPs from other nodes' blocks. These will be announced over BGP as more specific routes, so traffic to pods will always find its way to the right host.

### Exit from the node
We've finished our tour of the Frontend pod's host's view of the network. Remember exit out of the exit to return to the node.
```
exit
```

> __We now have a good understanding of Pod and Host networking.__

