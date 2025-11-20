# Ollama Demo

## 1. Create files

Create the yaml files for the new 
- namespace
- pv
- pvc
- deployment
- service
    - NodePort we selected 31500

## 2. Ensure it works

```bash
# MAC
curl http://192.168.0.112:31500/api/tags
# {"models":[]}%
```

## 3. Pull a model

```bash
curl -X POST http://192.168.0.112:31500/api/pull \
  -H "Content-Type: application/json" \
  -d '{
    "name": "qwen3-coder:latest"
  }'
```

Do it in **silent** if you don't want to see lots of outputs:
```bash
curl -s \
  -X POST http://192.168.0.112:31500/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "qwen3-coder:latest"}' | tail -n 1
```

### Check that it works
- List the tags of the model:
```bash
curl http://192.168.0.112:31500/api/tags
```

- **Run a COMPLETION wiht OpenAI syntax**:

```bash
curl -s http://192.168.0.112:31500/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -d '{
    "model": "qwen3-coder:latest",
    "messages": [
      { "role": "user", "content": "Explain how Kubernetes Deployments use ReplicaSets." }
    ]
  }' | jq
```

- **Streaming response**:

```bash
curl -N http://192.168.0.112:31500/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -d '{
    "model": "qwen3-coder:latest",
    "stream": true,
    "messages": [
      { "role": "user", "content": "Give me a TL;DR of the history of Unix." }
    ]
  }'
```

## 4. Delete the pod (test to see if model persist)

Delete the pod to see if the model persist 

```bash
kubectl delete pod -n ollama -l app=ollama
# wait until it recreates
kubectl get pods -n ollama
```

# Stop the Ollama pod

```bash
kubectl scale deployment ollama -n ollama --replicas=0
```

# Rollouts

```bash
kubectl apply -f ollama-rollout.yaml
kubectl apply -f ollama-service.yaml
```

```bash
kubectl get rollouts -n ollama
kubectl argo rollouts get rollout ollama-rollout -n ollama --watch

# Service
kubectl get svc -n ollama
```

Run inference:
```bash
curl http://192.168.0.112:31501/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -d '{
    "model": "qwen3-coder:latest",
    "messages": [
      { "role": "user", "content": "What is the area of a circle of radii pi" }
    ]
  }'
```

Stop:
```bash
kubectl scale rollout ollama-rollout -n ollama --replicas=0

```