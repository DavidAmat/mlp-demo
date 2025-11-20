# Docker Remote Build (Mac -> Ubuntu)

This guide outlines how to build Docker images on a remote Ubuntu machine from your Mac, leveraging Ubuntu's resources.

## 1. Ubuntu Machine Setup

Edit Docker daemon configuration with `sudo nano /etc/docker/daemon.json`
```json
{
    "data-root": "/mnt/ssd2/docker",
    "runtimes": {
        "nvidia": {
            "args": [],
            "path": "nvidia-container-runtime"
        }
    },
    "insecure-registries": [
        "192.168.0.112:5000"
    ],
    "hosts": ["unix:///var/run/docker.sock", "tcp://192.168.0.112:2375"]
}
```

Then to avoid conflicting hosts:
```bash
# 1) Create the drop-in directory (it may not exist)
sudo mkdir -p /etc/systemd/system/docker.service.d

# 2) Create an override to clear -H fd:// and let daemon.json "hosts" take effect
sudo tee /etc/systemd/system/docker.service.d/override.conf >/dev/null <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --containerd=/run/containerd/containerd.sock
EOF

# 3) Reload systemd and restart Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 5) Check TCP is listening on 2375 (since hosts is in daemon.json)
sudo ss -lntp | grep 2375
```
## 2. Mac Machine Setup

```bash
# 1. Set DOCKER_HOST environment variable
export DOCKER_HOST="tcp://192.168.0.112:2375"

# To make it persistent, add the above line to ~/.zshrc or ~/.bashrc, then:
source ~/.zshrc # or source ~/.bashrc

# 2. Verify connection to remote Docker daemon
docker info
```

In ubuntu:
```bash
# Make sure we run again the registry since we have restarted
docker start registry
```

## 3. Remote Image Build, Tag, and Push (from Mac)

```bash
# --- MAC --- #

# 1. Build the image for linux/amd64 on the Ubuntu machine
docker build --platform linux/amd64 -t gpu-inference-demo:latest .

# 2. Tag the image for your local registry (which is on Ubuntu)
docker tag gpu-inference-demo:latest 192.168.0.112:5000/metaflow-gpu-demo:latest

# 3. Push the image to your local registry (from Ubuntu's Docker daemon)
docker push 192.168.0.112:5000/metaflow-gpu-demo:latest
```
