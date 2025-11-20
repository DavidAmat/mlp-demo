# ArgoCD and MLP GitOps

We will 


## Create GitOps repo

```bash
projects
mkdir mlp-gitops
cd mlp-gitops
git init
mkdir -p projects/fastapi-rollouts-cd-demo
touch projects/fastapi-rollouts-cd-demo/rollout.yaml
touch projects/fastapi-rollouts-cd-demo/service.yaml
```

Edit files:
- `nano projects/fastapi-rollouts-cd-demo/rollout.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: fastapi-rollouts-cd-demo
  namespace: argo
spec:
  replicas: 1
  revisionHistoryLimit: 2
  selector:
    matchLabels:
      app: fastapi-rollouts-cd-demo
  template:
    metadata:
      labels:
        app: fastapi-rollouts-cd-demo
    spec:
      containers:
        - name: fastapi-rollouts-cd-demo
          image: 192.168.0.112:5000/fastapi-demo:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
  strategy:
    canary:
      steps:
        - setWeight: 50
        - pause: { duration: 30 }
        - setWeight: 100

```
- `nano projects/fastapi-rollouts-cd-demo/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-rollouts-cd-demo
  namespace: argo
spec:
  type: NodePort
  selector:
    app: fastapi-rollouts-cd-demo
  ports:
    - name: http
      port: 8080
      targetPort: 80
      nodePort: 32220

```


## Patch Argo CD Service

```bash
kubectl patch svc argocd-server -n argocd \
  -p '{
    "spec": {
      "type": "NodePort",
      "ports": [
        {
          "port": 443,
          "targetPort": 8080,
          "nodePort": 30443
        }
      ]
    }
  }'
```

Then 
```bash
kubectl get svc argocd-server -n argocd

# Access:
# https://192.168.0.112:30443
```



```bash

```