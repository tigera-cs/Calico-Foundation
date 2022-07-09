#!/bin/bash

kubectl delete -f 3-allow-felix-agent.yaml 
kubectl delete -f 2-hep.yaml
kubectl delete -f 1-failsafe.yaml
kubectl delete -f pod.yaml
