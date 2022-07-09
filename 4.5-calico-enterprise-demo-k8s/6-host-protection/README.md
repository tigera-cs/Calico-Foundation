## Host Protection

This labs delivers a great feature of Calico Enterprise 3.0 where-in a user can create automatic Hostendpoint resources for each cluster node. All HEP contains the same labels and IP addresses as its corresponding node. In this lab, we will examine how to protect a Host node by creating an HEP resouce and by allowing a certain pod to communicate with host - only on specific port by leveraging the Calico Network Policies. 

Here the created pod will be able to communicate with host only on port 10001.

### Steps
1. Execute the scipt hep.sh, this will create Automatic Hostendpoints resources, test Pod and will apply Network policies to allow communication between pod and Host over Port 10001.
```
    cd  6-host-protection/
    ./hep.sh
```
2. Now open two terminal, login to master node. Here we will be using netcat tool to setup a chat socket between pod and host.
a.  In terminal one, execute the following command. This will create a netcat chat on port 10001.
```
    nc -l -p 10001
```
b. In terminal two, open the pod with the following command.
```
    kubectl exec -it sender -n dev -- bash
```
c. After pod login, execute the following command. This will try to connect the pod to nc socket over port 10001. Write any chat messages.
```
    nc 10.0.0.10 10001
```
The chat message should be seen on other terminal.

d. Try to replicate steps a,b,c with port 10002. This shouln't work, as the pod to host communication is not allowed on any other port.

Execute the following script to cleanup the lab

```
   ./cleanup.sh
```
