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

```bash
kubectl -n argo get svc argo-server

# UBUNTU
kubectl -n argo port-forward --address 0.0.0.0 svc/argo-server 2746:2746

# UBUNTU
# Health checks
curl -vk https://localhost:2746/healthz
curl -vk https://localhost:2746/ | head -n 40

# On Mac
# Use always as LOGIN the middle button
https://192.168.0.112:2746/
```

# Fix RBAC so the wait container can write WorkflowTaskResults

Required because `quick-start-minimal.yaml` does NOT include RBAC for Argo v3.7.x CRDs.

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


# Workflow Manifest

Use the controller’s service account:

- Namespace: argo
- ServiceAccount: argo

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: argo-counter-
  namespace: argo
spec:
  serviceAccountName: argo
  entrypoint: counter
  templates:
    - name: counter
      container:
        image: 192.168.0.112:5000/argo-counter:latest
        command: ["entrypoint"]
        args: ["main"]
```

Submit it 
```bash
argo submit -n argo argo-counter-wf.yaml --watch
```

# Visualize logs

Argo uses:

- main — your actual workload
- wait — Argo's sidecar
- init — init container

```bash
kubectl logs -n argo argo-counter-xxxxx

# If your pod has multiple containers:
kubectl logs -n argo argo-counter-xxxxx -c main
```

# Clean Argo pods (finished)

```bash
kubectl delete pods -n argo --all
```

# Delete Argo namespace

```bash
# kubectl delete namespace argo --ignore-not-found

```