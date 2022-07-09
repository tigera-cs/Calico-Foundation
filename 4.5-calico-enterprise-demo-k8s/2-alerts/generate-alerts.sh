#/bin/bash
# create crown-space namespace used by the demo script
kubectl create ns crown-space
# set env var pointing to pull engg pull secret file
PULL_SECRET_PATH=$HOME/.docker/config.json
# create engg pull secret
kubectl -n crown-space create secret generic tigera-pull-secret \
  --from-file=.dockerconfigjson=$PULL_SECRET_PATH \
  --type=kubernetes.io/dockerconfigjson

# check whether tigera-pull-secret already exists in tigera-intrusion-detection namespace and delete it if exists
if [ ! -f $(kubectl -n tigera-intrusion-detection get secrets -o jsonpath='{.items[?(@.metadata.name=="tigera-pull-secret")].metadata.name}') ]; then
  kubectl -n tigera-intrusion-detection delete secret tigera-pull-secret
fi
# create new secret using engg team pull secret data
kubectl -n tigera-intrusion-detection create secret generic tigera-pull-secret \
  --from-file=.dockerconfigjson=$PULL_SECRET_PATH \
  --type=kubernetes.io/dockerconfigjson

python trigger-threatdef-features.py --glob-alert
