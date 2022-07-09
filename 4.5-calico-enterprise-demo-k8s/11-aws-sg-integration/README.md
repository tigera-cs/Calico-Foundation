# AWS SG Integration

This lab focuses on the integration of VPC security group with Calico Network policies.

The network security that Calico provides in Kubernetes cluster is great, however it is primarily focused on the kubernetes cluster itself. A common use-case for Calico however, is to build a kubernetes cluster that can interact with other Amazon hosted resources, such as EC2 and RDS instances. The native protection for those resources is the VPC’s Security Group filtering.

The problem with this, however, is that, by default, VPC Security Groups can only be applied to EC2 instances. Therefore, if you wanted to allow some subset of your pods access to an Ec2 or RDS instance, for example, you would have to allow that access from all of your EKS worker nodes, thereby allowing ALL your EKS pods access to that RDS instance. 

That’s probably not what you want. Luckily, one of the capabilities that Calico Enterprise enables is the integration of the VPC Security Group mechanism and Kubernetes/Calico network policy.

## Setup Steps

1. We have should have a running Kubernetes cluster with aws cloud provider.

2. Install AWS Security Group Integration with the help of AmazonCloudIntegration resource and controller. This creates multiple security policies in different tiers like sg-remote, sg-local and some metadata tier. We have multiple failsafe, ingress and other similar policies.

3. Till now we have a running Calico Enterprise cluster with AmazoncloudIntegration resource.

4. Create a Security Group protect_sa_sg in the same VPC with HTTP and SSH protocol ingress rule.

5. Create an EC2 instance within same VPC and with same subnet created above. Create this EC2 instance as a webserver. We need to follow the script for the same.

&nbsp;&nbsp;&nbsp;&nbsp; ```sudo apt-get update -y```

&nbsp;&nbsp;&nbsp;&nbsp; ```sudo apt-get install apache2 -y```

&nbsp;&nbsp;&nbsp;&nbsp; ```sudo service httpd start```

&nbsp;&nbsp;&nbsp;&nbsp; ```echo "<html><body>Welcome to Setec Astronomy</body></html>" | sudo tee /var/www/html/index.html```

6. Launch 2 test pods in the cluster and try to communicate with newly created Ec2 instance. (Test pod yamls should be provided on the setup during trainings)-> This should work.

7. We now need to limit it to certain pods with specific permissions. So we will Tighten up the security group.

8. Create a new security group allow_sa_sg with no inbound rule. 

9. Modify the protect_sa_sg group by removing ssh rule and editing the http rule to just allow traffic from allow_sa_sg security group.

10. We will now annonate pod1 with the allow_sa_sg security group. Now from test Pod1 try to access the EC2 instance. This should be successful. It verifies that only pods with allow_sa_sg annotation have network access to the additional EC2 instance.

&nbsp;&nbsp;&nbsp;&nbsp; ```kubectl annotate pod <test1 pod name> aws.tigera.io/security-groups='["<sg-ID>"]'```

11. Try the same test from Pod2 -> This shouldn't work. As the annotation isn't done for this pod.

We have now protected the VPC resource on a per-pod basis using VPC security groups.
