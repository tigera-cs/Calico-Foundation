kubectl delete -f 1-policy-workflow/application-hardening-policies/development-policies/
kubectl delete -f 1-policy-workflow/application-hardening-policies/production-policies
kubectl delete -f 1-policy-workflow/application-hardening-policies/staging-policies
kubectl delete -f 0-infrastructure/
sleep 20
