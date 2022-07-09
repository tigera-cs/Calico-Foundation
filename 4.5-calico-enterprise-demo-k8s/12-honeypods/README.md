# Honeypods

Honeypods are basically customizable set of canary pods placed in a cluster such that no valid endpoint/resource should ever attempt to access or make connections. If any resource like pod/ node reach the Honeypods, then that resource is assumed to be compromised. Honeypod may be used to detect resources enumeration, privilege escalation, data exfiltration, denial of service and vulnerability exploitation attempts.

#### In this lab we are focusing on the following usecases:
1. IP Enumeration
2. Exposed Service(Simulated)
3. Exposed Service(nginx)
4. Vulnerable Service(MySQL)

## Setup steps
1. Navigate to Honeypods manifets directory. Apply the sample_honeypod manifest to create different types on honeypods. For training these are available on the cluster.
2. Create a secret used to download Honeypods and attacker container images.

&nbsp;&nbsp;&nbsp; ```kubectl create -f honeypod_sample_setup.yaml```

3. Try to attack the honey pods using service ip from master node or from any attacker pod. We are simulating the connection from a attacker pod.

&nbsp;&nbsp;&nbsp; ```kubectl create -f attacker/attacker.yaml```

#### Observation: Alerts for all the vulnerable Honeypods should be rendered on Tigera Manager UI.

This lab helps to identify the compromised Source Pods/Node in the kubernetes cluster. Also it informs the cluster administrator regarding any compromising resource in the cluster.

The Kibana dashboard will use the following visualizations:

Shows the Honeypods deployed and pods that has contacted it. Includes Namespace, Name, Dst port, etc. A line graph or timelion of sessions

