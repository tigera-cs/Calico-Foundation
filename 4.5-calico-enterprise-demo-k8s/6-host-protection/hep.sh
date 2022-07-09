#!/bin/bash
  
calicoctl patch kubecontrollersconfiguration default --patch='{"spec": {"controllers": {"node": {"hostEndpoint": {"autoCreate": "Enabled"}}}}}'

kubectl label nodes --all kubernetes-host=heps

kubectl apply -f pod.yaml

sleep 5

kubectl exec -it sender -n dev -- apt-get update

sleep 5

kubectl exec -it sender -n dev -- apt-get install telnet netcat iputils-ping -y

kubectl apply -f policies.yaml
