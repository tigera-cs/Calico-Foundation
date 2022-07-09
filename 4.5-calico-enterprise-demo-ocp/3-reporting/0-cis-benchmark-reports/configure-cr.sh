#!/bin/bash
set -x

# Below script configures the compliance-reporter-pod.yaml yaml with appropriate reporter-token secret name, report name and report start time in UTC 3339 format
cp compliance-reporter-pod-backup.yaml compliance-reporter-pod.yaml
export COMPLIANCE_REPORTER_TOKEN=`kubectl get secret -n tigera-compliance | grep tigera-compliance-reporter-token | awk 'NR==1{ print $1 }'`
echo $COMPLIANCE_REPORTER_TOKEN
sed -i -e "s?<COMPLIANCE_REPORTER_TOKEN>?$COMPLIANCE_REPORTER_TOKEN?g" compliance-reporter-pod.yaml
export TIGERA_COMPLIANCE_REPORT_NAME=daily-cis-results
sed -i -e "s?<TIGERA_COMPLIANCE_REPORT_NAME>?$TIGERA_COMPLIANCE_REPORT_NAME?g" compliance-reporter-pod.yaml
export TIGERA_COMPLIANCE_REPORT_START_TIME=`date --rfc-3339=seconds | sed 's/ /T/'`
sed -i -e "s?<TIGERA_COMPLIANCE_REPORT_START_TIME>?$TIGERA_COMPLIANCE_REPORT_START_TIME?g" compliance-reporter-pod.yaml
