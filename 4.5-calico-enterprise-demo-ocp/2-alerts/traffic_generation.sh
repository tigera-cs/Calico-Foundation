#! /bin/sh

kubectl apply -f sample-globalnetworkset.yaml
sleep 2
kubectl delete -f sample-globalnetworkset.yaml
FRONTEND_POD_IP=`kubectl get pods -n development -o wide| grep frontend | tail -1 | awk '{print $6}'`
BACKEND_POD=`kubectl get pods -n development -o wide| grep backend | tail -1 | awk '{print $1}'`

for i in `seq 1 200`; do kubectl exec -it $BACKEND_POD -n development -- curl $FRONTEND_POD_IP:80; done

