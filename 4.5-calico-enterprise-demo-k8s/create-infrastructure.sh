kubectl label node ip-10-0-0-11 labnode=worker1 --overwrite=true
kubectl label node ip-10-0-0-12 labnode=worker2 --overwrite=true
kubectl apply -f 0-infrastructure/

