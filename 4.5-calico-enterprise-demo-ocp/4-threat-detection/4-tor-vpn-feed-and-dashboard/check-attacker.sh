POD=$(kubectl get pod -l app=attack -n yaobank -o jsonpath="{.items[0].metadata.name}")

kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.ejr-vpn  -o jsonpath='{.spec.nets[10]}')
 kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.ejr-vpn  -o jsonpath='{.spec.nets[11]}')

kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.tor-bulk-exit-list  -o jsonpath='{.spec.nets[9]}')
kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.tor-bulk-exit-list  -o jsonpath='{.spec.nets[10]}')


