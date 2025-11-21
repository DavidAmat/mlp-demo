# TGI Demo

Read first the `01-p-hf-text-generation-inference.md`

Then go to `demo/hf-tgi-demo` and see the YAML files.

## Image

Let's pull the image and push it to the local repo

```bash
docker pull ghcr.io/huggingface/text-generation-inference:2.4.0
docker tag ghcr.io/huggingface/text-generation-inference:2.4.0 \
  192.168.0.112:5000/tgi:2.4.0
docker push 192.168.0.112:5000/tgi:2.4.0
```

## PV
We assume we have followed previous markdown doc and have downloaded HF model in `/mnt/ssd2/hf/Llama-3.2-3B-Instruct`.

```bash
kubectl apply -f tgi-pv.yaml
kubectl apply -f tgi-pvc.yaml
kubectl apply -f tgi-rollout.yaml
kubectl apply -f tgi-service.yaml
```

Make sure in the rollouts we reference the pushed image: `192.168.0.112:5000/tgi:2.4.0`

Watch:
```bash
# Run Argo Rollout Dashboard
kubectl argo rollouts dashboard

# Or
kubectl -n argo get pods -w
```

Chat completions:
```bash
# MAC
curl http://192.168.0.112:32229/health
curl http://192.168.0.112:32229/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "model": "local",
        "messages": [
          {"role": "user", "content": "Who is the singer of Mr Blue Sky song ?"}
        ],
        "max_tokens": 100
      }'
```

# Stop it
```bash
kubectl scale rollout tgi-rollout -n argo --replicas=0
```



# IMPORTANT about GPU usage of multiple services

The way Minikube (and standard Kubernetes) handles the resource nvidia.com/gpu: 1 is through the NVIDIA Device Plugin. When a Pod, like your Ollama Rollout, requests nvidia.com/gpu: 1 under its resource limits, the Kubernetes Scheduler treats this as a **reservation** (request = limit = 1 GPU).

The scheduler will only place this Pod on a node (in your case, the single Minikube node) that the Device Plugin has advertised as having at least one available GPU.

Once the Pod is scheduled, that specific GPU is marked as allocated to the Pod's CGroup.

This means that even if the container isn't actively running a calculation, the GPU count drops to zero for scheduling purposes.

To launch a second service (like your TGI Rollout) that also requires nvidia.com/gpu: 1, the scheduler sees "0/1 GPUs available" and keeps the second Pod in the Pending state.

The rule is simple: Kubernetes cannot share non-partitionable resources like a full GPU card. To launch the TGI service, you must first scale down the competing Pod (Ollama) to release the GPU resource back to the Node's available pool.

When we do:
```bash
kubectl describe node david 

# Resource           Requests    Limits
#   --------           --------    ------
#   cpu                850m (2%)   0 (0%)
#   memory             240Mi (0%)  340Mi (0%)
#   ephemeral-storage  1Gi (0%)    1Gi (0%)
#   hugepages-1Gi      0 (0%)      0 (0%)
#   hugepages-2Mi      0 (0%)      0 (0%)
#   nvidia.com/gpu     1           1

```

## Scale down to free resources
To free the resource reserved by the Pod, you must scale the managing controller (the Rollout in your case) down to zero replicas.
```bash
kubectl scale rollout ollama-rollout -n ollama --replicas=0
```

## Who is the pod using the GPU

```bash
kubectl get pods --all-namespaces \
  -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.namespace}{"\t"}{.spec.containers[*].resources.limits.nvidia\.com/gpu}{"\n"}{end}' \
  | awk -F'\t' '$3 == "1"'
```