#!/bin/bash

kubectl delete -f policies.yaml
kubectl delete -f pod.yaml
kubectl label nodes --all kubernetes-host-
calicoctl patch kubecontrollersconfiguration default --patch='{"spec": {"controllers": {"node": {"hostEndpoint": {"autoCreate": "Disabled"}}}}}'
