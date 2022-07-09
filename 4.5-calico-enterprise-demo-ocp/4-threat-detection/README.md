# Lab 4: Threat Detection Labs 

Lab objective : To Create Zone-based policy management, detect and quarantine the rouge application running in storefront namespace, try accessing malicious IPs and detect them using GlobalThreatFeeds in Alerts section of Tigera Manager UI.

Lab tasks

Setup required infrastructure by creating the necessary resources. Here we create `yaobank` and `storefront` namespace and deploy application as shown

![microservice-architecture](img/microservice-architecture.jpg)

Execute the below command to create the infrastructure

```
./setup.sh
```

Once we have our required infrastructure in place we will be performing the following labs

1. Zone Based Policy
2. Rouge Detection
3. Trace and block suspicious IPs
4. Blocking Tor, VPN feed 

All the labs are created in individual directories along with their READMEs. Navigate to `1-Zone-Based-Policy` directory for the first lab.



Once done with all 4 labs, cleanup the created setup using the following script

```
./cleanup.sh
```


