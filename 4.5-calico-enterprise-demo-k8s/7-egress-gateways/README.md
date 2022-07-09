# Direct outbound traffic through egress gateways

## Value

An egress gateway acts as a transit pod for the outbound application traffic that is configured to use it. As traffic leaving the cluster passes through the egress gateway, its source IP is changed to that of the egress gateway pod, and the traffic is then forwarded on.

More details are available at [Direct outbound traffic through egress gateways](https://docs.tigera.io/security/threat-detection-and-prevention/tor-vpn-feed-and-dashboard)

Below are the steps to create and configure egress gateway, we will also test the functionality using netcat.

## Prerequisite
Make sure you have a standalone node running for verification purpose. This node should not be a part of kubernetes cluster.

## Enable egress gateway support 

In the default `FelixConfiguration`, set the `egressIPSupport` field to `EnabledPerNamespaceOrPerPod`

```bash
kubectl patch felixconfiguration.p default --type='merge' -p \
    '{"spec":{"egressIPSupport":"EnabledPerNamespaceOrPerPod"}}'
```
Create a namespace where we will deploy our `egress-gateway` and a `sample-client` pod

```
kubectl create ns egress-ns
```


## Provision an egress IP pool

Apply the following manifest that creates a `ippool` resource from which the IP address for `egress-gateway` will be allocated. Here we create a pool with cidr `10.10.13.0/31`

```
calicoctl apply -f egress-ippool.yaml
```

## Copy pull secret into egress gateway namespace
Identify the pull secret that is needed for pulling Calico Enterprise images, and copy this into the namespace where you plan to create your egress gateways. It is typically named tigera-pull-secret, in the calico-system namespace, in our case the namespace will be `egress-ns`

```
kubectl get secret tigera-pull-secret --namespace=calico-system --export -o yaml | \
   kubectl apply --namespace=egress-ns -f -
```

## Deploy egress gateway

Use a Kubernetes Deployment to deploy a group of egress gateways, using the egress IP Pool. Apply the below manifest.

```
kubectl apply -f eg-deploy.yaml

kubectl get pods -n egress-ns -o wide
```
Once the `egress-gateway` pod is up and running use the above command to get the details of the node on which the `egress-gateway` is running.

Our next step is to add the route entry of `ippool` cidr that comes via the host on which the `egress-gateway` is present.

```
sudo ip route add 10.10.13.0/31 via <node-ip> dev eth0
```

Apply the manifest on the kubernetes cluster that creates a `sample-client` pod in the `egress-ns` namespace. We will use this pod to test connection to the server on standalone node.

```
kubectl apply -f sample-pod.yaml
```

Once the route entry and sample-client pod is added we will now test the connection by creating a `netcat server` on the standalone node and initiate a connection from the `sample-client` pod.

On the standalone host run the following command, make sure you have the port specified open in the security group. In our case the port is 8089

```
sudo netcat -v -l -k -p 8089
```

Now on the Kubernetes cluster, run the following command to check connectivity. Replace the <server IP> with the private IP of standalone host.

```
kubectl exec sample-client -n egress-ns -- nc <server IP> 8089 </dev/null
```

Once this command is executed, on the server (standalone host) observe the <source IP> being one of the IPs of the egress IP pool that you provisioned.
