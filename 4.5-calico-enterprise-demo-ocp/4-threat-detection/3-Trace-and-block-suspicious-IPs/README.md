# Lab 4.3 : Trace and Block Suspicious IPs


1. In `3-Trace-and-block-suspicious-IPs` directory glimpse over `suspicious-ip-threatfeed.yaml` and `feodo-block-policy.yaml` to understand the GlobalThreatFeed being used and the policy to block traffic to the GlobalNetworkSet. The manifest `suspicious-ip-threatfeed.yaml` is already applied during infrastructure setup.

Details of the manifests:

---
The `suspicious-ip-threatfeed.yaml` GlobalThreatFeed pulls a ipblocklist and creates an alert if any of the IP address is being accessed by endpoint in the cluster. We have labeled the `globalNetworkSet` in the manifest as `threatfeed=feodo`.This label is then used as a selector in the policy that blocks traffic to these IP addresses.

The `feodo-block-policy.yaml` is a `GlobalNetworkPolicy` in the `security` tier that denies the any egress traffic towards the GlobalNetworkSet or ipblocklist using the above mentioned selector.

---
2. Execute the below script to generate traffic to random IP in the NetworkSet, this should create an `Alert` of type `Suspicious IP detected` by `name: attack-*` which is the source pod trying to access malicious IP. More details available at : [Trace and block suspicious IPs](https://docs.tigera.io/security/threat-detection-and-prevention/suspicious-ips)

```
./check-attacker-C_C.sh
```

3. Our next step is to remediate the attack, we achieve this by creating a Global Network Policy. Use the following command to apply the GlobalNetworkPolicy.
```
./remediate-threat-feed.sh
```

Observe `Alert` of type `Suspicious IP detected` on Tigera Manager UI.
