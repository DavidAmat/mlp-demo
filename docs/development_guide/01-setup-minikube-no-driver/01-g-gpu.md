# Installing NVIDIA Container Toolkit and Device Plugin in cluster

If we try to see if a Pod can locate the GPU of our host machine, we will not succeed out of the box.
We need the following installation.


## 1. Install NVIDIA Container Toolkit for Containerd

```bash
# On Ubuntu host
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

## 2. Configure Containerd for NVIDIA Runtime
```bash
# Configure containerd
sudo nvidia-ctk runtime configure --runtime=containerd
sudo systemctl restart containerd
```

## 3. Install NVIDIA Device Plugin
```bash
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

## 4. Update Your Metaflow Configuration
```bash
@resources(cpu=2, memory=8192, gpu=1)  # Add gpu=1
@step
def check_gpu(self):
    # ... existing code
```