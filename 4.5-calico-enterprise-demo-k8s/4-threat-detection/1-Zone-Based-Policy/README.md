# Lab 4.1 : Zone-based access policy management

Let’s see the security of our cluster in default state. And then we build out the security from the ground up, just like you build your network.
```
./NetworkStatus.sh
```

So you can see that every service is able to connect to every other service, irrespective of namespace. Of course, it is not acceptable. If we wear the security architect’s hat, we’ve assets of different business values. So we need to group them in zones. Commonly used zones are DMZ, Trusted and Restricted. Let’s apply the zones to the cluster and see what happens.
```
./SecureFirewallZones.sh
```

So now we can see that we’ve compartmentalized the namespace traffic. So a service in frontend cannot speak to service in Yaobank. Or a Customer service cannot speak to Database service. Of course, DMZ is open access for all services. This is very powerful. You achieve this by simply building your policies on labels. And then apply those labels to the pods. This is declarative policy and have the power to cut down your firewall rules our factor of 10 or more. Let us see what attacker has access to.
```
./NetworkStatus.sh
```

So this makes sense. Attacker is able to access database as they are in the same zone.

Businesses evolve, so security should never be a bottleneck for an agile business. Storefront team want to roll out a Bank-Info service. This service will need to be able to fetch customer data from Database service of YaoBank.
```
./NewServiceStorefront.sh
```
So w/ just 1 policy, now bank info service can get data from Database. Here is the important part - this policy is controlled by security admin, and NOT by storefront or yaobank admin. We achieve this by a capability “policy tiers” in Calico Enterprise. As a security admin, this makes it extremely simple to offload your firewall rules to Calico Enterprise, and also segregate controls for agile development.
```
./SecureBankInfoService.sh
```

Retest the connectivity when the application is authorized to talk to database by the Security team.
```
./NewServiceStorefront.sh
```



