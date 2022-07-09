import time
import subprocess
import os
import sys
from threading import Timer
import argparse
import re

#-----------------------------arg parser----------------------------------------#

parser = argparse.ArgumentParser()
optional = parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
optional.add_argument('--glob-feeds', action='store_true', default=False,
                    dest='gtf_switch',
                    help='set Global Threat Feeds configuration')
optional.add_argument('--glob-report', action='store_true', default=False,
                    dest='comp_switch',
                    help='set Compliance configuration')
optional.add_argument('--glob-alert', action='store_true', default=False,
                    dest='ga_switch',
                    help='set GlobalAlert configuration')
optional.add_argument('--configure-dga', action='store_true', default=False,
                    dest='dga_switch',
                    help='DGA Detection configuration, after 5 mins execute --run-dga')
optional.add_argument('--setup-honeypod', action='store_true', default=False,
                    dest='hp_switch',
                    help='setup Honeypods')
optional.add_argument('--all', action='store_true', default=False,
                    dest='all_switch',
                    help='Triggers Threat Feeds, Compliance Reporting, Global Alerts and configures DGA detection')
optional.add_argument('--run-dga', type=str, default='',
                    dest='dga_run_switch',
                    help='Run DGA job: Execute after 5 mins of running --configure-dga')

parser._action_groups.append(optional)
args = parser.parse_args()

if args.all_switch:
  args.gtf_switch = True
  args.comp_switch = True
  args.ga_switch = True
  args.dga_switch = True
  args.hp_switch = True

if args.gtf_switch == False and args.comp_switch == False and args.ga_switch == False and args.dga_switch == False and args.hp_switch == False and args.dga_run_switch == '':
  print '''ERROR: One of the optional argument must be set\n
  GlobalThreatFeeds:   --glob-feeds
  GlobalAlerts:        --glob-alert
  GlobalReport:        --glob-report
  DGA Detection:       --configure-dga (Execute --run-dga separately after 5min to run dga detection job)
  Honeypod:            --setup-honeypod
  All above features:  --all
  Trigger DGA job      --run-dga <Manager URL> (run separately after 5min of executing --configure-dga)

Usage:
  python trigger-threatdef-features.py --glob-feeds --glob-alert
  python trigger-threatdef-features.py --configure-dga
  python trigger-threatdef-features.py --all
  python trigger-threatdef-features.py --run-dga https://127.0.0.1:9443\n'''
  sys.exit()

#------------------check aggregation and flush interval------------------------#

def check_aggregation():
  result = execute_kubectl('kubectl describe felixconfiguration default')
  if re.search(r'Flow Logs File Aggregation Kind For Allowed:\s*[12]', result):
    print '\n## Aggregation level is set properly'
  else:
    print '''ERROR: Minimum aggregation level needs to be 1 - Use command:\nkubectl edit felixconfiguration default \nAdd following lines into manifest under 'spec':\n
  flowLogsFileAggregationKindForAllowed: 1
  flowLogsFlushInterval: 15s
  dnsLogsFlushInterval: 15s'''
    sys.exit()
  if re.search(r'Flow Logs Flush Interval:', result):
    print '## Flow Logs Flush Interval is set properly'
  else:
    print "ERROR: Flow Log Flush Interval needs to be 2 seconds - Use command 'kubectl edit felixconfiguration default' \nAdd line into manifest under spec: \nflowLogsFlushInterval: 15s"
    sys.exit()
  time.sleep(1)

#------------------------------kubectl-command-execution-----------------------#

def execute_kubectl(cmd):
  time.sleep(1)
  try:
    try:
      p = subprocess.Popen(
                [cmd], 
                stdout = subprocess.PIPE,
                shell = True)
      timer = Timer(8, p.kill)
      try:
        timer.start()
        #p.wait()
        (result, error) = p.communicate()
        print 'ended'
      finally:
        timer.cancel()
    except ValueError:
      pass
  except subprocess.CalledProcessError as e:
        sys.stderr.write(
            "common::run_command() : [ERROR]: output = %s, error code = %s\n"
            % (e.output, e.returncode))
  return result

if __name__ == "__main__":
  if args.dga_run_switch != '':
    if args.gtf_switch == True or args.comp_switch == True or args.ga_switch == True or args.dga_switch == True:
      print 'Instruction:\nUse --run-dga alone without any other options after 5 min of executing --configure-dga'
      sys.exit()
    if re.match("^https://.*\w$", args.dga_run_switch):
      print '##Login into Calico Enterprise Kibana using: ', args.dga_run_switch
      result = execute_kubectl("kubectl -n tigera-elasticsearch get secret tigera-secure-es-elastic-user -o yaml | grep elastic: | awk '{print $2}' | base64 --decode")
      cmd = 'curl -k -c cookie.txt "' + args.dga_run_switch + '''/tigera-kibana/api/security/v1/login" -H "accept: application/json, text/plain, */*" -H "kbn-version: 7.3.2" -H "content-type: application/json;charset=UTF-8" -H "sec-fetch-site: same-origin" -H "sec-fetch-mode: cors" -H "accept-encoding: gzip, deflate, br" --data-binary '{"username":"elastic","password":"''' + result + '''"}' --compressed --insecure'''
      results = execute_kubectl(cmd)
      print results
      print '##Running DGA job'
      results = execute_kubectl("curl -k -b cookie.txt '" + args.dga_run_switch + "/tigera-kibana/api/console/proxy?path=_watcher/watch/dga-watch/_execute&method=POST' \
                                    -X POST -H 'content-length: 0' -H 'kbn-version: 7.3.2' -H 'accept-encoding: gzip, deflate, br' -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
                                    --compressed --insecure")
      print results
      results = execute_kubectl("rm cookie.txt")
      sys.exit()
    else:
      print 'Use valid URL e.g. https://127.0.0.1:9443'
      print 'no / at end'
      sys.exit()

  #Check aggregation
  check_aggregation()
  #-------------------------------Initial POD Networkset deployment configuration----------------------------#

  initial_deployment ='''- <<EOF
kind: Pod
apiVersion: v1
metadata:
  name: attacker-pod
  namespace: crown-space
  labels:
    app: attacker
spec:
  imagePullSecrets:
  - name: tigera-pull-secret
  containers:
  - name: attacker-container
    image: quay.io/tigera/attacker-pod:pre-release

---

kind: Pod
apiVersion: v1
metadata:
  name: priv-crown-pod
  namespace: crown-space
  labels:
    app: crown-app
spec:
  imagePullSecrets:
  - name: tigera-pull-secret
  containers:
  - name: crown-container
    image: quay.io/tigera/attacker-pod:pre-release
EOF'''

  #---------------------------------GlobalAlert configuration-----------------------------------#

  global_alert = '''- <<EOF
apiVersion: projectcalico.org/v3
kind: GlobalNetworkSet
metadata:
  name: metadata-api
spec:
  nets:
  - 169.254.169.254

---

apiVersion: projectcalico.org/v3
kind: GlobalAlert
metadata:
  name: policy.globalnetworkset
spec:
  description: "Alerts on any changes to global network sets"
  summary: "[audit] [privileged access] change detected for \${objectRef.resource} \${objectRef.name}"
  severity: 100
  period: 5m
  lookback: 5m
  dataSet: audit
  query: (verb=create OR verb=update OR verb=delete OR verb=patch) AND "objectRef.resource"=globalnetworksets
  aggregateBy: [objectRef.resource, objectRef.name]
  metric: count
  condition: gt
  threshold: 0

---

apiVersion: projectcalico.org/v3
kind: GlobalAlert
metadata:
  name: network.lateral.originate
spec:
  description: "Alerts when pods with a specific label (app=crown-app) initiate connections to other workloads within the cluster"
  summary: "[flows] [lateral movement] \${source_namespace}/\${source_name_aggr} with label app=crown-app initiated connection"
  severity: 100
  period: 5m
  lookback: 5m
  dataSet: flows
  query: '"source_labels.labels"="app=crown-app" AND proto=tcp AND action=allow AND reporter=src AND NOT dest_name_aggr="metadata-api" AND NOT dest_name_aggr="pub" AND NOT dest_name_aggr="kse.kubernetes"'
  aggregateBy: [source_namespace, source_name_aggr]
  field: num_flows
  metric: sum
  condition: gt
  threshold: 0

---

apiVersion: projectcalico.org/v3
kind: GlobalAlert
metadata:
  name: network.lateral.access
spec:
  description: "Alerts when pods with a specific label (app=crown-app) accessed by other workloads within the cluster"
  summary: "[flows] [lateral movement] \${source_namespace}/\${source_name_aggr} has accessed pod with label app=crown-app"
  severity: 100
  period: 5m
  lookback: 5m
  dataSet: flows
  query: '"dest_labels.labels"="app=crown-app" AND proto=tcp AND action=allow AND reporter=dst'
  aggregateBy: [source_namespace, source_name_aggr]
  field: num_flows
  metric: sum
  condition: gt
  threshold: 0

---

apiVersion: projectcalico.org/v3
kind: GlobalAlert
metadata:
  name: network.cloudapi
spec:
  description: "Alerts on access to cloud metadata APIs"
  summary: "[flows] [cloud API] cloud metadata API accessed by \${source_namespace}/\${source_name_aggr}"
  severity: 100
  period: 5m
  lookback: 5m
  dataSet: flows
  query: '(dest_name_aggr="metadata-api" OR dest_ip="169.254.169.254" OR dest_name_aggr="kse.kubernetes" ) AND proto="tcp" AND action="allow" AND reporter=src AND (source_namespace="crown-space")'
  aggregateBy: [source_namespace, source_name_aggr]
  field: num_flows
  metric: sum
  condition: gt
  threshold: 0
EOF'''

  #we will be using pull threatfeed method for quick deployment
  #---------------------------GlobalThreatFeeds-IP-n-domain configuration---------------------------#

  global_threat_feed ='''- <<EOF
apiVersion: projectcalico.org/v3
kind: GlobalThreatFeed
metadata:
  name: global.threat.domains
spec:
  content: DomainNameSet
  pull:
    http:
      url: https://raw.githubusercontent.com/Dawsey21/Lists/master/main-blacklist.txt

---

apiVersion: projectcalico.org/v3
kind: GlobalThreatFeed
metadata:
  name: global.threat.ipfeodo
spec:
  pull:
    http:
      url: https://feodotracker.abuse.ch/downloads/ipblocklist.txt
  globalNetworkSet:
    labels:
      feed: feodo

---

apiVersion: projectcalico.org/v3
kind: GlobalThreatFeed
metadata:
  name: tor-bulk-exit-list
spec:
  pull:
    http:
      url: https://check.torproject.org/cgi-bin/TorBulkExitList.py?ip=1.1.1.1
  globalNetworkSet:
    labels:
      feed: tor

---

apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: default.block-feodo
spec:
  tier: default
  selector: app=='crown-app'
  types:
  - Egress
  egress:
  - action: Deny
    destination:
      selector: feed == 'feodo'
  - action: Allow
EOF'''

  #------------------------------Compliance Hourly Reporting configuration--------------------------------#

  global_reports ='''- <<EOF
apiVersion: projectcalico.org/v3
kind: GlobalReport
metadata:
  name: hourly-tigera-policy-audit
spec:
  reportType: policy-audit
  schedule:  0 * * * *

---

apiVersion: projectcalico.org/v3
kind: GlobalReport
metadata:
  name: hourly-networkacess-report
  labels:
    deployment: production
spec:
  reportType: network-access
  endpoints:
    namespaces:
      names: ["tigera-manager", "tigera-fluentd", "tigera-elasticsearch", "tigera-intrusion-detection", "default"]
  schedule: 0 * * * *

---

apiVersion: projectcalico.org/v3
kind: GlobalReport
metadata:
  name: hourly-inventory-report
  labels:
    deployment: production
spec:
  reportType: inventory
  endpoints:
    namespaces:
      names: ["tigera-manager", "tigera-fluentd", "tigera-elasticsearch", "tigera-intrusion-detection", "default"]
  schedule: 0 * * * *

---

apiVersion: projectcalico.org/v3
kind: GlobalReport
metadata:
  name: hourly-cis-results
  labels:
    deployment: production
spec:
  reportType: cis-benchmark
  schedule: 0 * * * *
  cis:
    highThreshold: 100
    medThreshold: 50
    includeUnscoredTests: true
    numFailedTests: 5
EOF'''

  #----------------------------------Deploy Initial confguration---------------------------------#

  #create namespace
  print '\n###Initial Deployment namespace, pod, networkset\n'
  print '\n#Creating namespace "crown-space"'
  cmd = 'kubectl create namespace crown-space'
  result = execute_kubectl(cmd)
  print result
  print "\n#namespace 'crown-space' created\n"
  print "\n#check Globalnetworkset metadata-api exists"
  result = execute_kubectl("kubectl delete globalnetworkset.projectcalico.org/metadata-api")

  #create pods
  print '\n#Deploying pods and networkset'
  cmd = 'kubectl apply -f ' + initial_deployment
  result = execute_kubectl(cmd)
  print result
  if ' unchanged' not in result:
    print '\n###Waiting 60 seconds to complete POD deployments...'
    time.sleep(60)
  result = execute_kubectl('kubectl get po -n crown-space -o wide')
  print result
  time.sleep(5)
  print '\n#Pod and networkset deployment complete\n'

  print '\n#Getting IP of pods'
  result = execute_kubectl("kubectl describe pod priv-crown-pod -n crown-space | grep IP: | grep -v /32 | awk '{print $2}' | uniq")
  crown_ip = result.strip()
  result = execute_kubectl("kubectl describe pod attacker-pod -n crown-space | grep IP: | grep -v /32 | awk '{print $2}' | uniq")
  attackr_ip = result.strip()
  print crown_ip, attackr_ip

  # configure DGA
  if args.dga_switch:
    print '\n\n### Installing DGA...\n'
    dga_manifest='''- <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: elastic-dga-detection-installer
  namespace: tigera-intrusion-detection
spec:
  template:
    spec:
      restartPolicy: OnFailure
      imagePullSecrets:
      - name: tigera-pull-secret
      containers:
      - name: install
        image: quay.io/tigera/dga-detection-job-installer:pre-release
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          runAsNonRoot: true
        env:
          - name: USER
            valueFrom:
              secretKeyRef:
                key: username
                name: tigera-ee-installer-elasticsearch-access
          - name: PASSWORD
            valueFrom:
              secretKeyRef:
                key: password
                name: tigera-ee-installer-elasticsearch-access
          - name: START_XPACK_TRIAL
            value: "true"
          - name: ELASTIC_HOST
            value: tigera-secure-es-http.tigera-elasticsearch.svc
          - name: ELASTIC_PORT
            value: "9200"
          - name: ES_CA_CERT
            value: /certs/es-ca.pem
          - name: KB_CA_CERT
            value: /certs/kb-ca.pem
          - name: KIBANA_HOST
            value: tigera-secure-kb-http.tigera-kibana.svc
          - name: KIBANA_PORT
            value: "5601"
          - name: ELASTIC_ACCESS_MODE
            value: serviceuser
          - name: ELASTIC_SSL_VERIFY
            value: "true"
          - name: ELASTIC_USER
            valueFrom:
              secretKeyRef:
                key: username
                name: tigera-ee-installer-elasticsearch-access
          - name: ELASTIC_USERNAME
            valueFrom:
              secretKeyRef:
                key: username
                name: tigera-ee-installer-elasticsearch-access
          - name: ELASTIC_PASSWORD
            valueFrom:
              secretKeyRef:
                key: password
                name: tigera-ee-installer-elasticsearch-access
          - name: AMOUNT_OF_DATA_FOR_DGA_ANALYSIS
            # use elasticsearch time units
            value: "1h"
          - name: UNINSTALL_ONLY
            value: "false"
          - name: DETECTION_INTERVAL
            value: "1800s"
        volumeMounts:
          - mountPath: /certs/es-ca.pem
            subPath: es-ca.pem
            name: es-certs
          - mountPath: /certs/kb-ca.pem
            subPath: kb-ca.pem
            name: kb-certs
      volumes:
        - name: es-certs
          secret:
            defaultMode: 420
            items:
              - key: tls.crt
                path: es-ca.pem
            secretName: tigera-secure-es-http-certs-public
        - name: kb-certs
          secret:
            defaultMode: 420
            items:
              - key: tls.crt
                path: kb-ca.pem
            secretName: tigera-secure-kb-http-certs-public
EOF'''
    dga_domains ='''
skguqgqmeawgacek.org
ogugsemgcwkikuci.org
ciyesemmsmqgqeoy.org
aeyyuemcegqaqkiq.org
iumqwioaqogmkeeo.org
myuisiiawiawoaec.org
skmqmowessacayok.org
qgaksukkgmgiaiwy.org
eimsoegkiwwikiim.org
ciiwkocycesyaqou.org
mcmmwoggcuucuaci.org
ywqesweaekmgukws.org
wwomycammcaumwgm.org
kuqmmusuuauokciw.org
uoaeikckoyickoqw.org
qkgiaagikuukeces.org
ocueuquwgyemkgue.org
ogiwasskoaegkeci.org
gqocicsgguuqiaqc.org
uoieysecsecqiigs.org
usiquyskegeockuy.org
kywgamwumkkwuyys.org
iqmqeceiaggskkwa.org
qgamsmscmwcowcwg.org
qkciskycoguumcks.org
gmmswwwskiuceeau.org
gqoeyiwmgqosgacc.org
mcooaoumciuqogec.org
qgwasmacckemykmc.org
iuaiqmkuayeqqacm.org
ocggggewymsasmoe.org
skoyssouimisasmm.org
ciesqommgwiuoqmq.org
qguyiiyiaowegqmy.org
socqemwqwuiksoms.org
wwwmkiuuyskkgmeq.org
ocoswgyeiswsayiw.org
qgekiiekkykgcgsw.org
mywmsuywcmieeuwu.org
mykmcgqscoawiasa.org
gqasoaegsecousmg.org
mcceqowicqwusyoq.org
wwmwqcuemwyawsag.org
qkuugssiaokiiqqu.org
mciwgymeeymyogqe.org
ocyecmmekkiqeuia.org
qkogkmgwakyeyocg.org
skgaqoomeswuiamm.org
eiagmwsqcigmscak.org
yagguysuokequswc.org
gqieiqogeqeimyws.org
mcwiewaiamiumwea.org
mjagsgshmgbj.com
mypejerweaaa.net
nokibvfrnyuk.biz
acgruhakytea.ru
ngbdbcgtfsik.org
ckqsiwmhcymn.co.uk
poleorsqixqx.info
vklyhmkokivc.com
jogknhqxqham.net
xsvaucwlnnep.biz
lwqlbwdutmia.ru
elogysvigfqk.org
fbjkqnawmywq.co.uk
gtyhmiifjkyx.info
hjtledmtpefe.com
attnlxgmrtim.net
bjordskbxnos.biz
cceoynsjuyqa.ru
drysqiwxbswg.org
rpmkxwgaphdr.co.uk
frnvxovbgxmh.info
sqkehgleyamb.com
gslphxbfpqvq.net
prrwdpfeslhl.biz
dtsidhufjcqb.ru
qspqmykicequ.org
euqcmqajsuak.co.uk
alujohymfxih.info
byvjyymsveob.com
bmsdxqeqoqrq.net
catdiirwfwxk.biz
xnavtaxqicmb.ru
ybbverlwyisu.org
yoxpdjduruvk.co.uk
acypnbqbibce.info
xhdavwpbsxrf.com
ljelvrvvktpy.net
albjigulekfk.biz
nncuibbgvgde.ru
vjimbpofvcvy.org
jljxbkuanxts.co.uk
xngvnytphoje.info
lphhntakykhx.com
gdlymhiyioly.net
hqmywcmcaado.biz
ihjiyqnjtbye.ru
jukijlrmlmqt.org
efqlrahdlsps.co.uk
fsrlculgdehi.info
gjouejmnwfdx.com
hwpuoeqqoqun.net
onmfauusmoay.biz
cpnqamktdfjo.ru
pokyjkhdttaa.org
dqlkjcwekkjp.co.uk
kvrmmnrjtgcc.info
xxsxmfhkkwlr.com
lwpgvdetblcd.net
yyqrvuturcls.biz
wjueqfnfcffo.ru
xwvebwblslli.org
xksxauapjkfp.co.uk
yxtxkmnvaqlj.info
sraldxkvjwhr.com
tfblnpxcadnl.net
tsxfmnwgqchs.biz
ugyfwfkmhinm.ru
ufduxueqphfg.org
ihegxpklhdda.co.uk
wjbekkqnycct.info
klcpkfwiqxan.com
qnicknbhwyhj.net
epjnkihcoufd.biz
srglwdnegtew.ru
gthwwxtyxpcq.org
dbltofwofxya.co.uk
eomtyabrwjqp.info
ffjdbujlosvn.com
gskdlpnogend.net
yjqbbxtfmpbd.biz
awrblsxiebss.ru
bnoknngcvkxq.org
cbpkxikfnvpg.co.uk
cspfloxrgflj.info
pwkoxgnstouu.com
dtnyuxdvpxus.net
qxiihpswdhee.biz
auurqtgwnoae.ru
nypbdlvxbxjp.org
bvsladlbwhjn.co.uk
oanumubckqsy.info
gcxtpyucexwn.com
hrsvnqiirskh.net
hdvnyiagnqgw.biz
isqpwanmbltq.ru
eedguedhlhli.org
ftxisvqnycyc.co.uk
ffbaeniluaur.info
guvccfvriuil.com
ikgujohspomu.net
vobevjnnrrlo.biz
koeevxmdbbaa.ru
xsynissxdeyt.org
gmlhotpxwxbp.co.uk
tqgqbovsybaj.info
iqjqbduiikou.com
vueanxbdknno.net
mtojnyeonhnh.biz
njjlltirpvls.ru
oxmsaijyytbm.org
pnhuxdncbiyx.co.uk
kvtvsemtuqcc.info
lloxqyqwwfan.com
marffnregdph.net
npmhdivhirns.biz
yqpanmkedqsn.ru
mukjaeafqacy.org
arntwcwokvso.co.uk
nvidjtmpxfca.info
uyuharuiofkp.com
idpqmjkjcotb.net
'''
    cmd = 'kubectl apply -f ' + dga_manifest
    result = execute_kubectl(cmd)
    print result
    if ' unchanged' not in result:
      print '\n#Waiting 1 min to deploy DGA pod\n'
      time.sleep(60)
    print '\n#Creating DGA domains file and copying to priv-crown-pod'
    file = open('dga_domains.txt', 'w')
    file.write(dga_domains)
    file.close()
    cmd = 'kubectl cp dga_domains.txt priv-crown-pod:/ -n crown-space'
    result = execute_kubectl(cmd)
    print result
    cmd = 'rm dga_domains.txt'
    result = execute_kubectl(cmd)
    print '\n#Querying 100+ DGA domains...\n'
    cmd = 'kubectl exec priv-crown-pod -n crown-space -- /usr/bin/dig -f dga_domains.txt'
    result = execute_kubectl(cmd)
    print '\n#Querying complete.\n'

  #configure GlobalAlerts
  if args.ga_switch:
    print '\n###Configuring GlobalAlerts'
    cmd = 'kubectl apply -f ' + global_alert
    result = execute_kubectl(cmd)
    print result
    print '\n###GlobalAlerts configured, Waiting 10s for backend\n'
    time.sleep(10)

  #Enable Compliance Hourly Reporting
  if args.comp_switch:
    print '\n###Configuring Compliance Hourly Reporting'
    cmd = 'kubectl apply -f ' + global_reports
    result = execute_kubectl(cmd)
    print result
    print '\n###Compliance Hourly Report configured\n'

  #configure GlobalThreatFeeds
  if args.gtf_switch:
    print '\n###Configuring Globalthreatfeed: IP and domain'
    cmd = 'kubectl apply -f ' + global_threat_feed
    result = execute_kubectl(cmd)
    print result
    print '\n###Globalthreatfeed configured. Waiting 30s to pull the feed\n'
    time.sleep(30)
    print '\n###Triggering GlobalThreatFeeds...'
    print '\n#malicious DNS queries'
    #result = execute_kubectl('kubectl exec priv-crown-pod -n crown-space -- /usr/bin/dig wcracked.com ')
    result = execute_kubectl('kubectl exec priv-crown-pod -n crown-space -- /usr/bin/dig jrcompanyhack.com ')
    #result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- /usr/bin/dig jrcompanyhack.com ')
    result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- /usr/bin/dig wcracked.com')

    print '\n#malicious IP requests'
    result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- /usr/bin/curl -m 5 85.204.116.191')
    result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- /usr/bin/curl -m 5 199.249.230.75')#tor
    result = execute_kubectl('kubectl exec priv-crown-pod -n crown-space -- /usr/bin/curl -m 5 91.121.251.65')#tor
    #result = execute_kubectl('kubectl exec priv-crown-pod -n crown-space -- /usr/bin/curl -m 5 107.172.251.159')#

  if args.ga_switch:
    print '\n###Triggering GlobalAlerts'
    print '#metadata API requests'
    result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- /usr/bin/curl -m 5 169.254.169.254')
    result = execute_kubectl('kubectl exec priv-crown-pod -n crown-space -- /usr/bin/curl -m 5 169.254.169.254')

    print '\n#Lateral Movements'
    result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- /usr/bin/curl -m 5 ' + crown_ip + ':3000')
    #result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- /usr/bin/curl -m 5 yahoo.com') #to internet
    result = execute_kubectl('kubectl exec priv-crown-pod -n crown-space -- /usr/bin/curl -m 5 ' + attackr_ip + ':3000')
  
  if args.hp_switch:
    print '\n###Setting Up Honeypods'
    print '\n#applying manifests'
    result = execute_kubectl('kubectl apply -f honeypod/honeypod_sample_setup.yaml')
    print '\n###Add tigera-pull-secret to tigera-internal namespace'
    print '\n###Wait 2min to deploy Honeypods'
    time.sleep(120)
    print '\n###Triggering Honeypod Alerts'
    result = execute_kubectl('kubectl exec attacker-pod -n crown-space -- bash /honeypod.sh')

  print '############### Finished - stopping ################'
  print '\n\nTo Cleanup the configuration from this script run following commands:'
  if args.ga_switch:
    print '\n###GlobalAlerts'
    print 'kubectl delete globalalert.projectcalico.org/policy.globalnetworkset'
    print 'kubectl delete globalalert.projectcalico.org/network.lateral.originate'
    print 'kubectl delete globalalert.projectcalico.org/network.lateral.access'
    print 'kubectl delete globalalert.projectcalico.org/network.cloudapi'
    print 'kubectl delete globalnetworkset.projectcalico.org/metadata-api'
  if args.gtf_switch:
    print '\n###Globalthreatfeeds'
    print 'kubectl delete globalthreatfeed.projectcalico.org/global.threat.domains'
    print 'kubectl delete globalthreatfeed.projectcalico.org/global.threat.ipfeodo'
    print 'kubectl delete globalnetworkpolicy.projectcalico.org/default.block-feodo'
  if args.comp_switch:
    print '\n###Compliance Reports'
    print 'kubectl delete globalreport.projectcalico.org/hourly-tigera-policy-audit'
    print 'kubectl delete globalreport.projectcalico.org/hourly-networkacess-report'
    print 'kubectl delete globalreport.projectcalico.org/hourly-inventory-report'
    print 'kubectl delete globalreport.projectcalico.org/hourly-cis-results'
  if args.hp_switch:
    print '\n###Honeypods'
    print 'kubectl delete -f honeypod/honeypod_sample_setup.yaml'
  print '\n###Initial Deployments'
  print 'kubectl delete pod/attacker-pod -n crown-space'
  print 'kubectl delete pod/priv-crown-pod -n crown-space'
  print 'kubectl delete namespace/crown-space'
  print '\n'
  if args.ga_switch:
    print '#####Instruction for globalalerts:'
    print "#Wait approx 6 mins for GlobalAlert to trigger. After that check 'alerts' page on Calico Enterprise Manager"
    print "#USE CMD: 'kubectl describe globalalerts <alert name>', 'Healthy: false' will change to 'true' when alert is triggered"
  if args.comp_switch:
    print '\n#####Instructions For globalreports'
    print "#Check 'Compliace Report' page after 30 mins on Enterprise Manager"
  if args.dga_switch:
    print "\n#####Instruction for DGA Detection:"
    print "# DGA Detection job runs every 1 hour"
    print "\n##### Manually Run DGA detection job"
    print "1. Wait 5 mins till DGA queries show up in Calico Enterprise Manager > Kibana > Discover > select from drop down: tigera_secure_ee_dns*"
    print "2. Go to Kibana > Dev Tools"
    print "3. Execute following command in console and check Calico Enterprise Manager Alert's page for detection (job takes upto 1 min to complete)"
    print "   POST _watcher/watch/dga-watch/_execute"
    print "\n\n#### Run DGA job via script"
    print "python trigger-threatdef-features.py --run-dga https://127.0.0.1:9443\n"
