# Set UP

```bash

ARGO_WORKFLOWS_VERSION="v3.7.3"  # or whatever version you choose
kubectl create namespace argo
kubectl apply -n argo -f "https://github.com/argoproj/argo-workflows/releases/download/${ARGO_WORKFLOWS_VERSION}/quick-start-minimal.yaml"

# Check status
kubectl -n argo get pods -l app=argo-server
kubectl -n argo get pods -w

# Install argo CLI
# https://github.com/argoproj/argo-workflows/releases/?utm_source=chatgpt.com
```

This creates:

- Namespace: argo
- Controller SA: argo
- Argo Server SA: argo-server
- Minimal RBAC (missing permissions for new CRDs)
You will run all workflows inside namespace argo, which is recommended for the minimal install.

Submit example
```bash
argo submit -n argo --watch https://raw.githubusercontent.com/argoproj/argo-workflows/main/examples/hello-world.yaml
```

# Accessing UI

Simplest way now (since you’re using Minikube with none driver) — just expose the Argo UI via NodePort so it’s reachable from your Mac:

Set a fixed NodePort
```bash
kubectl -n argo patch svc argo-server -p '{
  "spec": {
    "type": "NodePort",
    "ports": [{
      "port": 2746,
      "targetPort": 2746,
      "nodePort": 32045
    }]
  }
}'
kubectl -n argo get svc argo-server
```

Then access `https://192.168.0.112:32045/` in Mac

Try to ping from Mac The Workflows UI
```bash
curl -vk https://192.168.0.112:32045/healthz
```

# RBAC

# Fix RBAC so the wait container can write WorkflowTaskResults

Required because `quick-start-minimal.yaml` does NOT include RBAC for Argo v3.7.x CRDs.

You can paste this to **UBUNTU** to the `cluster` folder:
```yaml
# argo-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: argo-workflowtaskresults-role
  namespace: argo
rules:
  - apiGroups: ["argoproj.io"]
    resources:
      - workflowtaskresults
    verbs: ["create", "get", "list", "watch", "patch", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: argo-workflowtaskresults-binding
  namespace: argo
subjects:
  - kind: ServiceAccount
    name: argo
    namespace: argo
roleRef:
  kind: Role
  name: argo-workflowtaskresults-role
  apiGroup: rbac.authorization.k8s.io
```

Apply it `kubectl apply -f argo-rbac.yaml`


### Give permissions to the whole cluster
```bash
kubectl create clusterrolebinding argo-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=argo:argo
```

# MinIO

Expose it as a NodePort to port `32045`:

```bash
kubectl -n argo patch svc minio -p '{
  "spec": {
    "type": "NodePort",
    "ports": [
      {
        "name": "api",
        "port": 9000,
        "targetPort": 9000,
        "nodePort": 32046
      },
      {
        "name": "dashboard",
        "port": 9001,
        "targetPort": 9001,
        "nodePort": 32047
      }
    ]
  }
}'

# kubectl -n argo get svc
```

## Get the secrets

```bash
kubectl get secret my-minio-cred -n argo -o jsonpath='{.data.accesskey}' | base64 --decode
echo
# admin
kubectl get secret my-minio-cred -n argo -o jsonpath='{.data.secretkey}' | base64 --decode
echo
# password
```


## IMPORTANT! the New MinIO latest version

```bash
# 1. Get current MinIO deployment
kubectl -n argo get deployment minio -o yaml > minio.yaml

# 2. Edit the image to the latest MinIO release
#    Change:
#      quay.io/minio/minio:RELEASE....
#    To:
#      quay.io/minio/minio:latest
nano minio.yaml

# 3. Apply the updated deployment
kubectl -n argo apply -f minio.yaml

# 4. Delete the old MinIO pod so Kubernetes recreates it with the new image
kubectl -n argo delete pod -l app=minio

# 5. Verify the new pod is running
kubectl -n argo get pods -l app=minio -w
```

## Check accessible from Mac

```bash
AWS_ACCESS_KEY_ID=admin AWS_SECRET_ACCESS_KEY=password aws --endpoint-url http://192.168.0.112:32046 s3 ls
curl -I http://192.168.0.112:32046/minio/health/live
curl http://192.168.0.112:32046/minio/health/live
# should return nothing
nc -vz ubuntu 32046
```