#!/bin/sh
  
FRONTEND_POD_IP=`kubectl get pods -n development -o wide| grep frontend | tail -1 | awk '{print $6}'`
BACKEND_POD=`kubectl get pods -n development -o wide| grep backend | tail -1 | awk '{print $1}'`
BACKEND_POD_IP=`kubectl get pods -n development -o wide| grep backend | tail -1 | awk '{print $6}'`

#ping -w300 $FRONTEND_POD_IP & 
ping -i 0.4 -w300 $BACKEND_POD_IP &

for i in `seq 1 5000`; do kubectl exec -it $BACKEND_POD -n development -- curl $FRONTEND_POD_IP:80; done
