#!/bin/sh

FRONTEND_POD_IP=`kubectl get pods -n development -o wide| grep frontend | tail -1 | awk '{print $6}'`
BACKEND_POD=`kubectl get pods -n development -o wide| grep backend | tail -1 | awk '{print $1}'`

for i in `seq 1 5000`; do kubectl exec -it $BACKEND_POD -n development -- curl $FRONTEND_POD_IP:80; done

