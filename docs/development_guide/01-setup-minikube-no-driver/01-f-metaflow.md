# Set Up Metaflow

## Create a bucket

- Go to MinIO URL  `http://192.168.0.112:32047/buckets/`
- Create bucket `metaflow`

# Docker build and push

```bash
docker build --platform linux/amd64 -t 192.168.0.112:5000/metaflow-city-latency:latest .

# Verify
docker push 192.168.0.112:5000/metaflow-city-latency:latest

# Local registry
curl https://192.168.0.112:5000/v2/_catalog
curl https://192.168.0.112:5000/v2/metaflow-city-latency/tags/list
```

## Run demo Configs

Create a `.mteaflowconfig` folder in your demo/ folder:

```bash
{
    "METAFLOW_DEFAULT_DATASTORE": "local",
    "METAFLOW_DEFAULT_METADATA": "local"
}
```

```bash
{
  "METAFLOW_DEFAULT_DATASTORE": "s3",
  "METAFLOW_DATASTORE_SYSROOT_S3": "s3://metaflow",
  "METAFLOW_S3_ENDPOINT_URL": "http://192.168.0.112:32046",
  "METAFLOW_S3_ENDPOINT_URL_KUBERNETES": "http://minio.argo.svc.cluster.local:9000",
  "METAFLOW_DEFAULT_METADATA": "local",
  "METAFLOW_KUBERNETES_NAMESPACE": "argo",
  "METAFLOW_KUBERNETES_SERVICE_ACCOUNT": "argo",
  "METAFLOW_KUBERNETES_CONTAINER_REGISTRY": "192.168.0.112:5000",
  "METAFLOW_KUBERNETES_CONTAINER_IMAGE": "192.168.0.112:5000/metaflow-city-latency:latest"
}
```

### Run Locally

```bash
export METAFLOW_HOME=$(pwd)/.metaflowconfig
export AWS_ACCESS_KEY_ID=admin
export AWS_SECRET_ACCESS_KEY=password
export METAFLOW_PROFILE=local
python flow.py run
```

### Argo Metaflow execution

```bash
export METAFLOW_HOME=$(pwd)/.metaflowconfig
export AWS_ACCESS_KEY_ID=admin
export AWS_SECRET_ACCESS_KEY=password
export METAFLOW_PROFILE=argo

python flow.py argo-workflows create
python flow.py argo-workflows trigger
```


## Download locally artifacts

```bash
AWS_ACCESS_KEY_ID=admin \
AWS_SECRET_ACCESS_KEY=password \
aws s3 --endpoint-url http://192.168.0.112:32046 \
    cp s3://metaflow/CityLatencyFlow/data/ ./downloaded/ --recursive
```