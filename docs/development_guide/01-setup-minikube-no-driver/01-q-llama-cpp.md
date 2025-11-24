# Llama Cpp

```bash
docker pull ghcr.io/ggml-org/llama.cpp:server-cuda

sudo mkdir -p /mnt/ssd2/llamacpp
sudo chown 777 /mnt/ssd2/llamacpp 

docker run --rm \
  --gpus all \
  -e GGML_CUDA_ENABLE_UNIFIED_MEMORY=ON \
  -v /mnt/ssd2/llamacpp:/root/.cache/llama.cpp \
  -p 8033:8033 \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  --jinja \
  -c 0 \
  --host 0.0.0.0 \
  --port 8033 \
  -hf ggml-org/gpt-oss-20b-GGUF \
  --n-gpu-layers 999
```

The server is listening on Ubuntu at:

- http://127.0.0.1:8033
- http://192.168.0.112:8033 (from other machines on LAN)

## Test it
```bash
curl http://192.168.0.112:8033/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-20b",
    "messages": [
      {"role": "user", "content": "Who is the singer of Mr. Blue Sky song ?"}
    ],
    "temperature": 0.1
  }'
```

## Access the UI

```bash
# MAC
http://192.168.0.112:8033
```


# Deploy to Argo

```bash
# demo: llamacpp-demo
kubectl apply -f llamacpp-namespace.yaml
kubectl apply -f llamacpp-pv.yaml
kubectl apply -f llamacpp-pvc.yaml
kubectl apply -f llamacpp-rollout.yaml
kubectl apply -f llamacpp-service.yaml
```

Check the Rollout
```bash
kubectl argo rollouts get rollout llamacpp-rollout -n llamacpp
```

Or connect the Argo rollouts
```bash
kubectl argo rollouts dashboard
```

Access from Mac
```bash
# MAC
http://192.168.0.112:30833
```

Curl the service
```bash
curl http://192.168.0.112:30833/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-20b",
    "messages": [
      {"role": "user", "content": "Hello! Who are you?"}
    ]
  }'
```

# Shut down

```bash
kubectl scale rollout/llamacpp-rollout --replicas=0 -n llamacpp
```

# Status

```bash
kubectl get pods -n llamacpp

# Restart
kubectl scale rollout/llamacpp-rollout --replicas=1 -n llamacpp
kubectl argo rollouts get rollout llamacpp-rollout -n llamacpp
```