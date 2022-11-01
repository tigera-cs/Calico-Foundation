# 6. Automatic HostEndpoints Protection

In this lab, you will: \
6.1. Install a webserver that will be used as the target service \
6.2. Enable Automatic HostEndpoints for your kubernetes cluster nodes \
6.3. Configure a GlobalNetworkPolicy to allow traffic to the webserver \
6.4. Configure a HostEndpoint for the bastion host that will start to enforce the traffic

## 6.1. Emulate a running service

We will use netcat to simulate an application listening on port 7777 on the bastion node. Open a second tab to the lab (`http://<LABNAME>.lynx.tigera.ca`), and once logged in, execute the following command.

```
netcat -nvlkp 7777
```

Now get back to the original tab where you were working and test the connectivity to the server from your master node:

```
ssh control1
```
```
nc -zv 10.0.1.10 7777
```
```
Connection to 10.0.1.10 7777 port [tcp/*] succeeded!
```

Exit the master node, but keep running the service in your second tab as we will verify the connectivity again after implementing our Host Endpoint configuration.

## 7.3. Enable Automatic HostEndpoints for your kubernetes cluster nodes

Enable Automatic HostEndpoints by patching kubecontrollersconfiguration. 
We will use the automatic HostEndpoints from workers as the source in our GlobalNetworkPolicy that will protect the bastion node.

```
kubectl patch kubecontrollersconfiguration default --patch='{"spec": {"controllers": {"node": {"hostEndpoint": {"autoCreate": "Enabled"}}}}}'
```

## 7.4. Configure a GlobalNetworkPolicy to allow traffic to the webserver

Check the following globalnetworkpolicy. Notice how we select the bastion node by label type == 'bastion' or bastion = 'true'. This corresponds to the HostEndpoint we'll apply in the next step. Also notice how we allow traffic to port 7777 only from kubernetes nodes that have the label node-role.kubernetes.io/worker and allow traffic to port 80 from any source (this is needed to avoid lock up ourselves, as we access the lab through ttyd on that port).

```
kubectl get node -o=custom-columns=NAME:.metadata.name,LABELS:.metadata.labels
```
```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: platform.bastionfirewall
spec:
  egress:
  - action: Allow
    destination:
      ports:
      - 80
      - 443
    protocol: TCP
  ingress:
  - action: Allow
    destination:
      ports:
      - 7777
    protocol: TCP
    source:
      selector: has(node-role.kubernetes.io/worker)||egress-code == "red"||app == "app1"
  - action: Allow
    destination:
      ports:
      - 80
    protocol: TCP
    source: {}
  selector: type == "bastion"||bastion == "true"
  tier: platform
  types:
  - Ingress
  - Egress
EOF
```


Apply the HostEndpoint. Note that manual HostEndpoints are default deny. Anything that is not allowed by failsafes or GlobalNetworkPolicies will be denied.

```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: HostEndpoint
metadata:
  name: bastion
  labels:
    bastion: "true"
spec:
  interfaceName: "ens5"
  node: bastion
  expectedIPs:
  - 10.0.1.10
EOF
```

Test that traffic is being allowed only from a worker node

```
ssh worker1
```
```
nc -zv 10.0.1.10 7777
```
```
Connection to 10.0.1.10 7777 port [tcp/*] succeeded!
```

Try now from the control node, this test must fail:

```
ssh control1
```
```
nc -zv 10.0.1.10 7777
```

You can leave this second tab open, as we will use it in our next lab.
