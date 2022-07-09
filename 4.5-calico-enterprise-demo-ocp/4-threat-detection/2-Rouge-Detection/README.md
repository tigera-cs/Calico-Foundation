# Lab 4.2 : Detect and Quarantine Rouge endpoints

In this lab we will identify and visualize the level of access the rouge system has. We will then quarantine the rogue system after examining the behavior. Navigate to `2-Rouge-Detection` directory and execute the following script, the script triggers a rouge application deployment in the storefront namespace.
```
./DeployRogue.sh
```

The rouge application shall look as below once deployed.

![rouge-setup](img/rouge-setup.png)

Analyze the flow-logs and the reach of the rouge system on Tigera Manager UI.


Our next step is to quarantine the `rouge application` by labeling the pod appropriately using label `quarantine=true`. Execute the below script to achieve the same, the script  can be found in `2-Rouge-Detection` directory.

```
./QuarantineRogue.sh
```

This label enables the the `quarantine` policy in the `security` tier to `log` and `Deny` the traffic both ingress and egress those have label as `quarantine=true`, in this case the pod with name `rouge-*` gets quarantined.

Analyze the denial of packets once the application is quarantined on the Tigera Manager's `Flow Visualization` tab or `Dashboard`
