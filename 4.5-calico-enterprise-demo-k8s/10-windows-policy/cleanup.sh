#!/bin/bash
kubectl delete -f policy/k8s.allow-dns.yaml
kubectl delete -f policy/k8s.allow-iis-egress-to-nginx.policy.yaml
kubectl delete -f policy/k8s.allow-nginx-ingress-from-iis.yaml
kubectl delete -f policy/k8s.allow-netshoot-egress-to-iis.yaml
