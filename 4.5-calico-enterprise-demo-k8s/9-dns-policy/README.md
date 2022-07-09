# DNS Policies
This lab emphasises on how calico policy can allow/deny traffic from endpoints to destinations outside of the cluster. Here we are using domain names in policy to identify services residing outside the cluster. Domain names can include a wildcard (*), making it easier to manage large numbers of domains/sub-domains.
#### Ex. update.*.mycompany.com matches update.tools.mycompany.com
Domain names in policy rules are applicable only for Egress allow rules.
There are 3 ways of using domain names in policies.
 - Use domain names in a global network policy
 - Use domain names in a namespaced network policy
 - Use domain names in a global network set, reference the set in a global network policy
Here we are going to create a Globalnetworkpolicy and try to access the external domains.
## Steps
1. Creation of a nginx frontend pod with label app: frontend, which in our case is already created.
2. Create and apply a GlobalNetworkPolicy (DNS Policy) with destination domains. Here we are just allowing access to google.com and www.google.com
```
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: allow-egress-to-domains
spec:
  order: 1
  selector: app == 'frontend'
  types:
  - Egress
  egress:
  - action: Allow
    protocol: UDP
    destination:
      ports:
      - 53
      - dns
  - action: Allow
    destination:
      domains:
      - google.com
      - www.google.com
```
