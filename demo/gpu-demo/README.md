# GPU Inference Demo

Test GPU access from Kubernetes pods running Hugging Face model inference.

## Virtual Env

```bash
pyenv local 3.12.11
/Users/david/.pyenv/versions/3.12.11/bin/python -m venv venv
source venv/bin/activate

pip install metaflow
pip install kubernetes
```

## Quick Start

```bash
# Build and push image from Mac
docker build --platform linux/amd64 -t 192.168.0.112:5000/metaflow-gpu-demo:latest .
docker push 192.168.0.112:5000/metaflow-gpu-demo:latest

# Set environment
export METAFLOW_HOME=$(pwd)/.metaflowconfig
export AWS_ACCESS_KEY_ID=admin
export AWS_SECRET_ACCESS_KEY=password

# Run on Kubernetes/Argo
export METAFLOW_PROFILE=argo
python flow.py argo-workflows create
python flow.py argo-workflows trigger
```

