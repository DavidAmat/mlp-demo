FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Set non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system Python (3.10) and base tools
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Symlink python to python3
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Upgrade pip to latest version
RUN python -m pip install --upgrade pip

# CRITICAL: Install torch 2.4.1 with CUDA 12.4 support FIRST
# This must be done before Poetry to avoid dependency resolution conflicts
# Poetry doesn't handle torch's special CUDA index URLs well
RUN pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124

# Verify torch installation with CUDA support
RUN python -c "import torch; print(f'PyTorch: {torch.__version__}'); assert '2.4.1' in torch.__version__, 'Wrong torch version'"

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install remaining dependencies with pip
# Install transformers, accelerate, and other deps specified in pyproject.toml
# We use pip instead of Poetry to avoid torch version conflicts
RUN pip install \
    metaflow \
    "transformers>=4.51.0" \
    "accelerate>=0.20.3" \
    boto3 \
    pyyaml \
    kubernetes

# Copy flow file
COPY flow.py .

# Set environment variables for CUDA
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Verify installations
RUN python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

ENTRYPOINT ["python", "flow.py"]

