# Containers talking to NVIDIA card

It is not straighforward to have the Containers in Ubuntu talking to the host GPU of ubuntu.

I had to downgrade to Driver version `550.163.01` in my Ubuntu 25.04, which is CUDA Version 12.4

## NVIDIA Container Toolkit

```bash
# 1. Remove broken NVIDIA container toolkit installs
sudo apt purge -y nvidia-container-toolkit nvidia-container-runtime
sudo rm -rf /etc/nvidia-container-runtime
# sudo rm -f /etc/docker/daemon.json   # DO NOT DO THIS unless you want to regenerate the daemon.json
sudo systemctl restart docker
```

Configure repos and GPG keys
```bash
# 2. Add NVIDIA GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg   # add key

# 3. Add the correct NVIDIA repo list file (supported, contains Release file)
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list    # add repo
```

Then:
```bash
# 4. Install NVIDIA Container Toolkit
sudo apt update
sudo apt install -y nvidia-container-toolkit   # install runtime

# 5. Register NVIDIA runtime with Docker
sudo nvidia-ctk runtime configure --runtime=docker   # auto-write docker runtime config
sudo systemctl restart docker
```


## Dockerfile

```bash
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system Python (3.10) and base tools
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Symlink python to python3
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Install Poetry (with virtualenvs enabled)
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy only pyproject.toml for dependency resolution
COPY pyproject.toml .

# Generate poetry.lock (no dependency installation)
RUN poetry lock

# Default interactive shell
ENTRYPOINT ["/bin/bash"]
```

## Build and enter the container

```bash
# Build it
docker build -f Dockerfile.lock-generator -t gpu-demo-lock-generator .

# Enter
docker run -it --gpus all gpu-demo-lock-generator:latest
```

## Inside the container

```bash
# Install PyTorch (CUDA 12.4) inside the container
pip install torch==2.4.1+cu124 torchvision==0.19.1+cu124 torchaudio==2.4.1+cu124 \
  --extra-index-url https://download.pytorch.org/whl/cu124   # install correct CUDA 12.4 wheels

# Verify GPU is visible inside the container
nvidia-smi   # should show RTX 4090 and driver 550.163.01

# Verify torch sees CUDA
python3 - << 'EOF'     # torch.cuda.is_available() → True
import torch
print(torch.cuda.is_available())
EOF

# Allocate ~1GB tensor on GPU and test CUDA memory usage
python3 - << 'EOF'
import torch, time
x = torch.randn(250_000_000, device='cuda')   # ~1GB tensor
print("Allocated 1GB on GPU, check nvidia-smi")
time.sleep(30)
EOF
```

# Summary

We successfully set up a full end-to-end GPU-enabled workflow for a local Argo Workflows + Minikube environment running on an Ubuntu workstation, with a Mac acting purely as the client. We configured Docker on Ubuntu to expose its daemon over DOCKER_HOST so all image builds happen on the powerful Ubuntu machine, even when triggered from the Mac, and we pushed those images into a local registry. We then fixed NVIDIA GPU support inside containers by installing and correctly configuring the NVIDIA Container Toolkit, aligning container CUDA versions with the host driver version (after downgrading the Ubuntu drivers to match CUDA 12.4). With this alignment, we verified that containers could successfully access the host GPU, including through PyTorch, and confirmed that workflow steps inside Argo running on Minikube can detect and utilize the GPU. In short, we achieved a fully GPU-enabled, remotely controlled, containerized development and workflow execution pipeline across Mac → Ubuntu → Minikube