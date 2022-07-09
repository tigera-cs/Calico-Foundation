POD=$(kubectl get pod -l app=attack -n yaobank -o jsonpath="{.items[0].metadata.name}")

kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.feodo-tracker  -o jsonpath='{.spec.nets[11]}')
kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.feodo-tracker  -o jsonpath='{.spec.nets[12]}')
kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.feodo-tracker  -o jsonpath='{.spec.nets[13]}')
kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.feodo-tracker  -o jsonpath='{.spec.nets[4]}')
kubectl exec -ti $POD -n yaobank -c attacker -- curl --connect-timeout 5 -v http://$(kubectl get globalnetworkset threatfeed.feodo-tracker  -o jsonpath='{.spec.nets[15]}')

