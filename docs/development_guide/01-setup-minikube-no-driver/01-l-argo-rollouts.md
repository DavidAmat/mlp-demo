# Install Argo Rollouts
```bash
# https://argoproj.github.io/argo-rollouts/installation/
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml


kubectl get pods -n argo-rollouts
kubectl get crd | grep rollouts

brew install argoproj/tap/kubectl-argo-rollouts
```

# First rollout

- `fastapi-rollouts-demo.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: fastapi-rollouts-demo
  namespace: argo
spec:
  replicas: 1
  revisionHistoryLimit: 2
  selector:
    matchLabels:
      app: fastapi-rollouts-demo
  template:
    metadata:
      labels:
        app: fastapi-rollouts-demo
    spec:
      containers:
        - name: fastapi-rollouts-demo
          image: 192.168.0.112:5000/fastapi-demo:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
  strategy:
    canary:
      # Minimal canary strategy, just to show Rollouts in action
      steps:
        - setWeight: 50
        - pause: { duration: 30 }   # 30s pause at 50% traffic
        - setWeight: 100

---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-rollouts-demo
  namespace: argo
spec:
  type: NodePort
  selector:
    app: fastapi-rollouts-demo
  ports:
    - name: http
      port: 8080          # service port (inside cluster)
      targetPort: 80      # FastAPI container port
      nodePort: 32211     # fixed NodePort on Ubuntu host
```

Submit it:
```bash
# Submit a rollout
kubectl apply -f fastapi-rollouts-demo.yaml
```

# Verify 
```bash
kubectl get rollouts -n argo
kubectl argo rollouts get rollout fastapi-rollouts-demo -n argo --watch
kubectl get svc -n argo
```


```bash
# Access the dashboard in Mac
kubectl config set-context --current --namespace=argo

# RUN IT!!!
kubectl argo rollouts dashboard
```

# Get rollouts
```bash
kubectl get rollouts
```

# Test the API from Mac

```bash
curl -X POST http://192.168.0.112:32211/add \
  -H "Content-Type: application/json" \
  -d '{"x":3,"y":4}'
```
