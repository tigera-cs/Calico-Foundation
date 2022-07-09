# Policy Workflow for Calico for Windows

This lab covers allowing and blocking access from one set of application pods to another.

### Prerequisite: Allow DNS access for all Pods in default namespace.
```kubectl apply -f policy/k8s.allow-dns.yaml```
  
#### label kube-system namespace to target it in policies
```kubectl label ns kube-system dnshost=true```

```kubectl get ns kube-system --show-labels```
#### Apply DNS policy that targets kube-system namespace
```kubectl apply -f policy/k8s.allow-dns.yaml```

## Lab Scenarios 

### 1. Try accessing Linux pods (nginx) from windows pods (iis).
```IIS_POD=$(kubectl get pod -l run=iis -o jsonpath='{.items[*].metadata.name}')```

```nginx_svc_IP=$(kubectl get svc -l run=nginx-svc -o jsonpath='{.items[*].spec.clusterIP}')```

```kubectl exec -t $IIS_POD -- powershell -command 'iwr -UseBasicParsing  -TimeoutSec 5 http://<nginx_svc_IP>'```

This shoudln't be successfull.

### 2. Allow windows pods (iis) to access Linux Pod's (nginx).
#### Apply policy to allow only iis PODs to access nginx service
```kubectl apply -f policy/k8s.allow-iis-egress-to-nginx.policy.yaml```

```kubectl apply -f policy/k8s.allow-nginx-ingress-from-iis.yaml```
#### iis POD should be able to curl nginx-svc IP
```kubectl exec -t $IIS_POD -- powershell -command 'iwr -UseBasicParsing  -TimeoutSec 5 http://<nginx_svc_IP>'```
#### netshoot POD should not be able to curl nginx-svc
kubectl exec -t netshoot -- sh -c 'SVC=nginx-svc; curl -m 5 -sI http://$SVC 2>/dev/null | grep -i http'

### 3. Allow Linux Pod (netshoot) to access windows Pod (iis). Then deploy calico  ingress policy to prevent netshoot from accessing the iis Pods.
```kubectl apply -f policy/k8s.allow-netshoot-egress-to-iis.yaml```
### netshoot POD should be able to curl iis-svc

```kubectl exec -t netshoot -- sh -c 'SVC=iis-svc; curl -m 5 -sI http://$SVC 2>/dev/null | grep -i http'```

### 4. Execute the clean script to clean the applied policies.
``` ./cleanup.sh```

