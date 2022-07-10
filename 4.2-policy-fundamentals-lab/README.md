## 4.2. Network Policy - Fundamentals

In this 2nd lab, we will explore the use cases of NetworkPolicy and GlobalNetworkPolicy for pod and service communication.

In this lab you will:

* Simulate a compromise
* Create Kubernetes Network Policy to limit access
* Create a Global Default Deny and allow Authorized DNS
* Create a network policy to the rest of the sample application


### Simulate a compromise

First, let's start by simulating a pod compromise where the attacker is attempting to access the database from the compromised pod. We can simulate a compromise of the customer pod by just exec'ing into the pod and attempting to access the database directly from there.

Determine the customer pod name and assign it to an environment variable so that we can reference it later on.  

```
CUSTOMER_POD=$(kubectl get pod -l app=customer -n yaobank -o jsonpath='{.items[0].metadata.name}')
echo $CUSTOMER_POD
```

Verify that the output correctly references the pod. Execute into the pod to simulate a compromise.

```
kubectl exec -ti $CUSTOMER_POD -n yaobank -- bash
```
You are now logged in and ready to launch the attack.

From within the customer pod, attempt to access the database directly. The attack will succeed and the balance of all users will be returned. This is expected as there are no policies limiting access yet.

```
curl http://database:2379/v2/keys?recursive=true | python -m json.tool
```

Now, let's exit the pod and put some network policies in place.
```
exit
```

### Create Kubernetes Network Policy to limit access

We can use a Kubernetes Network Policy to protect the Database.

Examine and apply the following network policy. This policy allows access to the database on TCP port 2379 strictly from the summary pods.

``` 
kubectl apply -f -<<EOF
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: database-policy
  namespace: yaobank
spec:
  podSelector:
    matchLabels:
      app: database
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: summary
      ports:
      - protocol: TCP
        port: 2379
EOF

```

Repeat the attack commands again. This time the direct database access should fail. However, the customer frontend access from your browser should still work.

```
kubectl exec -ti $CUSTOMER_POD -n yaobank -- bash
```

```
curl http://database:2379/v2/keys?recursive=true | python -m json.tool
```
You should receive an output similar to the following. The curl will be blocked and return no data. You may need to CTRL-C to terminate the command.  

```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:--  0:00:19 --:--:--     0
```

Exit the customer pod.

```
exit
```

### Create a Global Default Deny and allow Authorized DNS

Now, let's introduce a Calico default deny GlobalNetworkPolicy, which applies throughout the cluster. 

Examine and apply the default deny policy.

```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: default-deny
spec:
  selector: all()
  types:
  - Ingress
  - Egress
EOF

```


Verify default deny policy

In the previous step, we only defined a network policy allowing ingress traffic from summary pods to the database pod. The rest of our pods should now be hitting default deny since there is no policy defined matching them.  

Lets try to see if basic connectivity works by logging into the customer pod and doing some tests.

```
kubectl exec -ti $CUSTOMER_POD -n yaobank -- bash
```

```
dig www.google.com
```

```
**root@customer-68d67b588d-pd9hn:/app# dig www.google.com

; <<>> DiG 9.10.3-P4-Ubuntu <<>> www.google.com
;; global options: +cmd
;; connection timed out; no servers could be reached**
```

The name resolution request above should time out and fail after around 15s because we do not have a policy in place to allow DNS traffic.

Exit the customer pod.

```
exit
```

Now, let's examine and apply policies, which allow DNS traffic to the cluster internal kube-dns and also allow kube-dns to communicate with anything.

```
kubectl apply -f -<<EOF
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: dns-allow
spec:
  order: 600
  selector: all()
  egress:
  - action: Allow
    protocol: UDP
    destination:
      ports:
      - 53
      selector: k8s-app == "kube-dns"
  - action: Allow
    protocol: TCP
    destination:
      ports:
      - 53
      selector: k8s-app == "kube-dns"
  - action: Deny
    protocol: UDP
    destination:
      ports:
      - 53
  - action: Deny
    protocol: TCP
    destination:
      ports:
      - 53
---
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: kubedns-allow-all
  namespace: kube-system
spec:
  order: 500
  selector: k8s-app == "kube-dns"
  egress:
  - action: Allow
  ingress:
  - action: Allow
    protocol: UDP
    destination:
      ports:
      - 53
  - action: Allow
    protocol: TCP
    destination:
      ports:
      - 53
EOF
```

The global policy allows all pods egress access to kube-dns and denies egress DNS requests to other DNS servers.  
The network policy allows ingress DNS requests to kube-dns.
Notice the policy order which is a functionnality of Calico that allows a deterministic sequential processing of policies.

Now, let's apply the policy and examine the impact. 

```
calicoctl apply -f 4.2-globalallowdns.yaml
```

Now repeat the same test and DNS lookups should be successful.

```
kubectl exec -ti $CUSTOMER_POD -n yaobank -c customer bash
```

```
dig www.google.com
```

Remember to exit from the kubectl exec of the customer pod by typing `exit`.
```
exit
```

### 4.2.4. Create a network policy to the rest of the sample application

We've now defined a default deny across all of the cluster, plus allowed DNS queries to kube-dns (CoreDNS). We also defined a specific policy for the `database` in section 4.2. 
But we haven't yet defined policies for the `customer` or `summary` pods.

#### 4.2.4.1. Verify cannot access Frontend

Try to access the Yaobank front end from your browser. The Yaobank app should timeout since we haven't created a policy for the `customer` and `summary` pods. So, in this case we are actually matching the default deny rule. 

### 4.2.4.2. Create policy for the remaining pods

Let's examine and apply a policy for all the Yaobank services.
```
more 4.2-more-yaobank-policy.yaml

kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: summary-policy
  namespace: yaobank
spec:
  podSelector:
    matchLabels:
      app: summary
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: customer
      ports:
      - protocol: TCP
        port: 80
  egress:
    - to: []

---

kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: customer-policy
  namespace: yaobank
spec:
  podSelector:
    matchLabels:
      app: customer
  ingress:
    - ports:
      - protocol: TCP
        port: 80
  egress:
    - to: []
```
Notice that the egress rules are excessively liberal, allowing outbound connection to any destination. While this may be required for some workloads, in most cases specific restrictive rules are required to limit cluster access. We will look at how this can be locked down further by the cluster operator or security admin in the next module.

```
kubectl apply -f 4.2-more-yaobank-policy.yaml
```

#### 4.2.4.3. Verify everything is now working
Now try accessing the Yaobank front end from the browser, it should work again. By defining the cluster wide default deny we've forced the user to follow best practices and define network policy for all the necessary microservices.


> __Congratulations! You have completed you fundamental Calico policies lab.__
