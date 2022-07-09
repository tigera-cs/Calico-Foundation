# Lab 4.4 : Trace anonymous communication using Tor-VPN feeds


1. In this lab we will be observing the `Alerts` we created for `vpn` and `tor` feeds. Go to `4-tor-vpn-feed-and-dashboard`and observe `ejr-vpn.yaml`, `tor-exit-feed.yaml` manifests that were used to create the `GlobalThreatFeeds`. These manifests are already applied during the infrastructure setup. More details are available at [Trace anonymous communication using Tor-VPN feeds](https://docs.tigera.io/security/threat-detection-and-prevention/tor-vpn-feed-and-dashboard)

Details of the manifests:

---
The `ejr-vpn.yaml` and `tor-exit-feed.yaml` GlobalThreatFeed pulls lists and creates an alert if any of the IP address is being accessed by endpoint in the cluster. We have labeled the `globalNetworkSet` in the manifests as `feed: ejr-vpn` and `feed: tor`.These labels are then used as a selector in the policy that blocks traffic to these IP addresses.

The `ejr-vpn-block-policy.yaml` and `tor-block-policy.yaml` is a `GlobalNetworkPolicy` in the `security` tier that denies the any egress traffic towards the GlobalNetworkSet or ipblocklist using the above mentioned selector.

---
2. Try accessing the IP addresses from the NetworkSets for tor and vpn cases. Execute the following script to generate traffic.

```
./check-attacker.sh
```

3. Our next step is to remediate the attack, we achieve this by creating a Global Network Policy. Use the following command to apply the GlobalNetworkPolicy.
```
./remediate-tor-vpn.sh
```

Cleanup the created setup using the following script in `4.5-calico-enterprise-demo` directory

```
./cleanup.sh
```
