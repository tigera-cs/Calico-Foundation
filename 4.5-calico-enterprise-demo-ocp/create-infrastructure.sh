j=0; for i in `kubectl get nodes | grep "worker" |  awk '{print $1}'` ; do kubectl label node $i labnode=worker$((j + 1)) --overwrite=true; j=$((j+1)) ; done
kubectl apply -f 0-infrastructure/

