#!/bin/bash
set -x

# Below script is responsible to configure and add necessary audit flags in /etc/kubernetes/manifests/kube-apiserver.yaml and restart the apiserver

sudo cp audit-policy.yaml /etc/ssl/certs/
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver-backup.yaml
sudo cp kube-apiserver.yaml /etc/kubernetes/manifests/
sudo kubeadm init
sudo rm -rf ~/.kube/config
sudo cp /etc/kubernetes/admin.conf ~/.kube/config
sudo chown ubuntu:ubuntu ~/.kube/config
sleep 10

. configure-cr.sh
