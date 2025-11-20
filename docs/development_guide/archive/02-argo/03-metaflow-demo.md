# Python env

```bash
pyenv local 3.12.11
/Users/david/.pyenv/versions/3.12.11/bin/python -m venv venv
source venv/bin/activate
```

# Run

```bash
python flow.py run
```


# Docker build and push

```bash
docker build \
  --platform linux/amd64 \
  -t 192.168.0.112:5000/metaflow-city-latency:latest .

# Verify
docker push 192.168.0.112:5000/metaflow-city-latency:latest

# Local registry
curl http://192.168.0.112:5000/v2/_catalog
curl http://192.168.0.112:5000/v2/metaflow-city-latency/tags/list
```

# Secrets of minIO

Run in Ubuntu
```bash
# UBUNTU
kubectl port-forward -n argo svc/minio 9000:9000 --address=0.0.0.0
```

```bash
kubectl get secret my-minio-cred -n argo -o jsonpath='{.data.accesskey}' | base64 --decode
echo
# admin
kubectl get secret my-minio-cred -n argo -o jsonpath='{.data.secretkey}' | base64 --decode
echo
# password
```

Make sure you can reach the minio from your Mac
```bash
# MAC
nc -vz ubuntu 9000
curl -v http://ubuntu:9000
```

## Create a bucket metaflow

- Access `http://192.168.0.112:9001/buckets/` from your Mac
- Create a new bucket `metaflow`


# Running locally

1. Configure

`config_local.json`
```json
{
    "METAFLOW_DEFAULT_DATASTORE": "local",
    "METAFLOW_DEFAULT_METADATA": "local"
}
  
```


2. Configure
`config_argo.json`
```json
{
  "METAFLOW_DEFAULT_DATASTORE": "s3",
  "METAFLOW_DATASTORE_SYSROOT_S3": "s3://metaflow",
  "METAFLOW_S3_ENDPOINT_URL": "http://ubuntu:9000",
  "METAFLOW_S3_ENDPOINT_URL_KUBERNETES": "http://minio.argo.svc.cluster.local:9000",
  "METAFLOW_DEFAULT_METADATA": "local",
  "METAFLOW_KUBERNETES_NAMESPACE": "argo",
  "METAFLOW_KUBERNETES_SERVICE_ACCOUNT": "argo",
  "METAFLOW_KUBERNETES_CONTAINER_REGISTRY": "192.168.0.112:5000",
  "METAFLOW_KUBERNETES_CONTAINER_IMAGE": "192.168.0.112:5000/metaflow-city-latency:latest"
}
```

3. Set the METAFLOW_HOME and PROFILE env variables to point to the json files
```bash
export METAFLOW_HOME=$(pwd)/.metaflowconfig
export AWS_ACCESS_KEY_ID=admin
export AWS_SECRET_ACCESS_KEY=password
```

4. Run locally (no Argo, no minikube)
```bash
export METAFLOW_PROFILE=local
python flow.py run
```

## Deploy to Argo

```bash
export METAFLOW_PROFILE=argo
python flow.py argo-workflows create
```

## Trigger execution

```bash
export METAFLOW_PROFILE=argo
python flow.py argo-workflows trigger

# Metaflow 2.19.7 executing CityLatencyFlow for user:david
# Validating your flow...
#     The graph looks good!
# Running pylint...
#     Pylint not found, so extra checks are disabled.
# Workflow citylatencyflow triggered on Argo Workflows (run-id argo-citylatencyflow-wbnxq)
```

# Configure Env variables

## Creatin a secret

```bash
kubectl create secret generic aws-credentials \
  --from-literal=AWS_ACCESS_KEY_ID=admin \
  --from-literal=AWS_SECRET_ACCESS_KEY=password \
  --namespace=argo
```

Adapt the `flow.py`:
```python
from metaflow import FlowSpec, kubernetes, resources, step

class CityLatencyFlow(FlowSpec):
    @kubernetes(secrets=["aws-credentials"])
    @resources(cpu=1, memory=1024)
    @step
    def start(self):
```

Delete and re-run the workflow
```bash
kubectl delete workflowtemplate citylatencyflow -n argo

# Run
export METAFLOW_HOME=$(pwd)/.metaflowconfig
export METAFLOW_PROFILE=argo
python flow.py argo-workflows create

# Trigger
python flow.py argo-workflows trigger
```



# Debugging ENV variables injection

## Run as test

```bash
kubectl run test-env \
  --rm -it \
  --restart=Never \
  -n argo \
  --image=192.168.0.112:5000/metaflow-city-latency:latest \
  --env="AWS_ACCESS_KEY_ID=admin" \
  --env="AWS_SECRET_ACCESS_KEY=password" \
  --command -- /bin/sh -c "env | grep AWS"
# AWS_ACCESS_KEY_ID=admin
# AWS_SECRET_ACCESS_KEY=password
# pod "test-env" deleted from argo namespace
```

## Inspect env variables

```bash
kubectl get workflowtemplate -n argo citylatencyflow -o yaml | grep -A20 "env:"
```

# Delete existing template

```bash
kubectl delete workflowtemplate citylatencyflow -n argo
```


# Kubectl

```bash
# Delete failed pods
kubectl delete pod --field-selector=status.phase==Failed -n argo
```
