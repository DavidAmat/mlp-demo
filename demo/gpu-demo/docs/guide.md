# GPU Inference Demo with Metaflow

## 1. Infrastructure Setup

Our infrastructure consists of a powerful Ubuntu workstation at IP 192.168.0.112 running Minikube with the none driver, meaning Kubernetes runs directly on the host using containerd as the container runtime. This setup provides proper host-level networking and direct access to hardware resources. Argo Workflows 3.7.3 is installed in the argo namespace and serves as the orchestration engine for Metaflow pipelines. MinIO provides S3-compatible storage for workflow artifacts, with its API exposed on NodePort 32046 and the web UI on NodePort 32047. A local HTTPS container registry runs at 192.168.0.112:5000, secured with mkcert TLS certificates trusted by both Ubuntu's containerd and the Mac Docker client. The Mac laptop acts purely as a remote kubectl client for cluster management and workflow submission.

Metaflow is configured with profile-based configurations stored in `.metaflowconfig` directories. The argo profile specifies S3 as the datastore with dual endpoint URLs: one for external access from the Mac (http://192.168.0.112:32046) and another for pods using internal cluster DNS (http://minio.argo.svc.cluster.local:9000). Workflows execute in the argo namespace using the argo service account with cluster-admin permissions. AWS credentials (admin/password) are passed as environment variables to enable artifact storage in MinIO.

## 2. What We Want to Build

The goal of this demo is to verify that Kubernetes pods running in our Minikube cluster can successfully access and utilize the GPU hardware from the underlying Ubuntu machine. Even though workloads run inside containers orchestrated by Kubernetes, we want to confirm that the containerized applications can detect, communicate with, and leverage the host GPU for compute-intensive tasks. This is critical for running machine learning inference workloads that require GPU acceleration.

We will create a Metaflow workflow that progresses through three stages: first, checking GPU availability by running diagnostic tools like nvidia-smi and verifying PyTorch's CUDA detection; second, loading a Hugging Face transformer model (GPT-2) and running text generation inference on the detected GPU; and third, aggregating the results and uploading them to MinIO. The test prompt will be "Explain what an LLM is" to generate a meaningful text output that demonstrates the GPU is functioning properly for inference workloads.

## 3. How We're Going to Do This

### GPU Passthrough Requirements

For Kubernetes pods to access the host GPU, several components must be configured correctly. The Ubuntu machine must have NVIDIA drivers installed and functional. Kubernetes needs the NVIDIA device plugin deployed to expose GPU resources to the scheduler. Pods must request GPU resources in their specifications and use CUDA-enabled container images. Since Minikube with the none driver runs directly on the host, GPU passthrough should be more straightforward than with virtualized drivers.

### Docker Image Strategy

The Dockerfile uses `nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04` as the base image, which provides CUDA runtime libraries, cuDNN for deep learning, and development tools. We install Python 3.10 and pip, then install PyTorch with CUDA support, the Transformers library for Hugging Face models, and Metaflow dependencies. The image includes environment variables like `NVIDIA_VISIBLE_DEVICES=all` and `NVIDIA_DRIVER_CAPABILITIES=compute,utility` to ensure GPU access. Building from the Mac requires the `--platform linux/amd64` flag for AMD64 compatibility, though GPU-specific libraries are architecture-independent once the base image is correct.

### Metaflow Configuration

We create a `.metaflowconfig` directory with profile configurations similar to the city-latency demo. The argo profile specifies the container registry, image tag, service account, and namespace. When running `python flow.py argo-workflows create` and `trigger`, Metaflow generates Argo Workflow YAML manifests and submits them to the cluster. Each step in the flow becomes a Kubernetes pod, and Argo orchestrates the execution sequence.

### Workflow Steps

The `start` step initializes the flow and sets the test prompt. The `check_gpu` step runs comprehensive GPU diagnostics: it executes nvidia-smi to see GPU hardware details, imports PyTorch and checks `torch.cuda.is_available()`, prints CUDA version and device count, and lists environment variables related to GPU visibility. The `run_inference` step loads the GPT-2 model from Hugging Face, automatically selecting GPU if available or falling back to CPU, runs text generation on the test prompt, measures load time and inference time, and captures the generated text. The `end` step aggregates all results into a summary JSON, saves it locally, and uploads it to MinIO at `s3://metaflow/gpu-inference-demo/gpu_inference_results.json`.

### Potential Issues and Solutions

If the GPU is not detected, common issues include missing NVIDIA drivers on Ubuntu, NVIDIA device plugin not installed in Kubernetes, pods not requesting GPU resources in their specs, or CUDA libraries in the container not matching host driver versions. The diagnostics step prints detailed information to help identify the specific problem. If nvidia-smi fails, it indicates the container cannot see the GPU device, likely due to missing device plugin or incorrect pod configuration. If PyTorch imports but CUDA is unavailable, the PyTorch installation may not include CUDA support, or there may be a driver/library version mismatch.

## Commands

### Build and Push Image

```bash
# From Mac, in demo/gpu-demo directory
docker build --platform linux/amd64 -t 192.168.0.112:5000/metaflow-gpu-demo:latest .
docker push 192.168.0.112:5000/metaflow-gpu-demo:latest

# Verify in registry
curl https://192.168.0.112:5000/v2/_catalog
curl https://192.168.0.112:5000/v2/metaflow-gpu-demo/tags/list
```

### Create Metaflow Configuration

Create `.metaflowconfig/config_argo.json`:

```json
{
  "METAFLOW_DEFAULT_DATASTORE": "s3",
  "METAFLOW_DATASTORE_SYSROOT_S3": "s3://metaflow",
  "METAFLOW_S3_ENDPOINT_URL": "http://192.168.0.112:32046",
  "METAFLOW_S3_ENDPOINT_URL_KUBERNETES": "http://minio.argo.svc.cluster.local:9000",
  "METAFLOW_DEFAULT_METADATA": "local",
  "METAFLOW_KUBERNETES_NAMESPACE": "argo",
  "METAFLOW_KUBERNETES_SERVICE_ACCOUNT": "argo",
  "METAFLOW_KUBERNETES_CONTAINER_REGISTRY": "192.168.0.112:5000",
  "METAFLOW_KUBERNETES_CONTAINER_IMAGE": "192.168.0.112:5000/metaflow-gpu-demo:latest"
}
```

Create `.metaflowconfig/config_local.json`:

```json
{
  "METAFLOW_DEFAULT_DATASTORE": "local",
  "METAFLOW_DEFAULT_METADATA": "local"
}
```

### Run Workflow

```bash
# Set environment variables
export METAFLOW_HOME=$(pwd)/.metaflowconfig
export AWS_ACCESS_KEY_ID=admin
export AWS_SECRET_ACCESS_KEY=password

# Run locally (will use CPU)
export METAFLOW_PROFILE=local
python flow.py run

# Run on Argo/Kubernetes (will attempt GPU)
export METAFLOW_PROFILE=argo
python flow.py argo-workflows create
python flow.py argo-workflows trigger
```

### Install NVIDIA Device Plugin (if needed)

If GPU is not detected in pods, install the NVIDIA device plugin:

```bash
# On Ubuntu or from Mac kubectl
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify plugin is running
kubectl get pods -n kube-system | grep nvidia

# Check if GPU is advertised as a resource
kubectl get nodes -o yaml | grep -i nvidia
```

### Monitor Workflow

```bash
# Watch workflow progress
argo list -n argo
argo get -n argo <workflow-name>
argo logs -n argo <workflow-name>

# Or via UI
open https://192.168.0.112:32045
```

### Download Results

```bash
# Download results from MinIO
AWS_ACCESS_KEY_ID=admin \
AWS_SECRET_ACCESS_KEY=password \
aws s3 --endpoint-url http://192.168.0.112:32046 \
    cp s3://metaflow/gpu-inference-demo/gpu_inference_results.json ./

# View results
cat gpu_inference_results.json
```

## Expected Output

If GPU is available, you should see:

- nvidia-smi showing GPU model, memory, and driver version
- `torch.cuda.is_available()` returning True
- GPU device count > 0 with device name (e.g., "NVIDIA RTX 4090")
- Inference running on GPU with faster execution times
- Generated text completing the prompt about LLMs

If GPU is not available, the workflow will still complete but fall back to CPU, with diagnostic information explaining why CUDA was not detected. This allows us to systematically troubleshoot the GPU passthrough configuration.


