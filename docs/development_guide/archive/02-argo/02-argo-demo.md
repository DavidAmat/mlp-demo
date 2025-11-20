
# Build and push
```bash
# MAC:  Build image  
docker build \
  --platform linux/amd64 \
  -t 192.168.0.112:5000/argo-counter:latest .

# MAC: Push to local registry
docker push 192.168.0.112:5000/argo-counter:latest

# MAC
curl http://192.168.0.112:5000/v2/_catalog
curl http://192.168.0.112:5000/v2/fastapi-demo/tags/list

# Test that you can pull it from minikube ssh
# UBUNTU
minikube ssh
docker pull 192.168.0.112:5000/argo-counter:latest
```

# Create the manifest

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: argo-counter-
  namespace: argo
spec:
  serviceAccountName: argo
  archiveLogs: true # Archive logs into minio
  entrypoint: counter
  templates:
    - name: counter
      container:
        image: 192.168.0.112:5000/argo-counter:latest
        command: ["entrypoint"]
        args: ["main"]

```

Submit
```bash
argo submit argo-counter-wf.yaml --watch
```

# Archiving logs

See the Minio service
```bash
kubectl get svc -n argo
# minio         ClusterIP   10.111.38.124    <none>        9000/TCP,9001/TCP   92m
# Port 9000 = MinIO API (S3-compatible)
# Port 9001 = MinIO Console (Web UI)
```

## Forward the MinIO Console to your Ubuntu host

```bash
# UBUNTU
kubectl port-forward svc/minio -n argo 9001:9001 --address 0.0.0.0
```

On mac: `http://192.168.0.112:9001`

Default credentials:
- username: admin
- password: password

## Minio Client

- Install minio client mac:
```bash
brew install minio/stable/mc
# mc --version
```

- Register Ubuntu minio from argo as a host
```bash
# UBUNTU
kubectl port-forward svc/minio -n argo 9000:9000 --address 0.0.0.0

# MAC
mc alias set argo http://192.168.0.112:9000 admin password
```


```bash
mc ls argo
mc ls argo/my-bucket/argo-counter-dspmc/
mc ls argo/my-bucket/argo-counter-dspmc/argo-counter-dspmc/

# Copy
mc cp argo/my-bucket/argo-counter-dspmc/argo-counter-dspmc/main.log logs/main.log
```