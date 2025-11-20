# Quick Guide

```bash
# Start
sudo systemctl start containerd
sudo CHANGE_MINIKUBE_NONE_USER=true minikube start --driver=none --container-runtime=containerd

# Stop
sudo systemctl stop kubelet
sudo systemctl stop containerd

# Full stop (Not needed)
sudo systemctl stop kubelet
sudo systemctl stop containerd
# sudo systemctl stop docker 2>/dev/null

# Adding insecure registry
sudo minikube config set insecure-registry "192.168.0.112:5000"
sudo systemctl restart containerd
```

# Set Up

We cannot properly communicate MinIO from metaflow to the MinIO pod while also allowing the Pods access the same IP of the Pod because the minikube was running under `Docker driver`.

Solution was to move Minikube to a `None` driver

# Commands

```bash
# --- Install required packages ---
sudo apt update
sudo apt install -y conntrack containernetworking-plugins containerd

# --- Install crictl ---
VERSION="v1.34.0"
wget https://github.com/kubernetes-sigs/cri-tools/releases/download/$VERSION/crictl-$VERSION-linux-amd64.tar.gz
sudo tar zxvf crictl-$VERSION-linux-amd64.tar.gz -C /usr/local/bin
rm crictl-$VERSION-linux-amd64.tar.gz

# --- Ensure CNI plugins exist in /opt/cni/bin ---
sudo mkdir -p /opt/cni/bin
sudo cp -r /usr/lib/cni/* /opt/cni/bin/

# --- Create containerd config (missing by default) ---
sudo mkdir -p /etc/containerd
sudo containerd config default | sudo tee /etc/containerd/config.toml >/dev/null

# --- Restart containerd ---
sudo systemctl restart containerd

# --- Disable fs protection needed by none-driver ---
sudo sysctl fs.protected_regular=0

# --- Delete any old kube/minikube configs ---
sudo rm -rf /home/david/.kube
sudo rm -rf /home/david/.minikube
sudo rm -rf /home/david/.minikube.bak
sudo rm -rf /root/.kube
sudo rm -rf /root/.minikube

# --- Start Minikube as root, but generate user configs ---
sudo CHANGE_MINIKUBE_NONE_USER=true minikube start --driver=none --container-runtime=containerd

# --- Create user kube folders ---
mkdir -p /home/david/.kube
mkdir -p /home/david/.minikube

# --- Copy configs from root (zsh-safe) ---
sudo cp -r /root/.kube/. /home/david/.kube/
sudo cp -r /root/.minikube/. /home/david/.minikube/

# --- Rewrite kubeconfig paths from /root → /home/david ---
sed -i 's|/root/.minikube|/home/david/.minikube|g' /home/david/.kube/config

# --- Fix permissions ---
sudo chown -R david:david /home/david/.kube /home/david/.minikube

# --- Test ---
kubectl get nodes

# Test from UBUNTU
sudo ss -tulnp | grep 8443
```

# Configure Mac client

```bash
mkdir -p ~/.kube
scp david@192.168.0.112:/home/david/.kube/config ~/.kube/config

rm -rf ~/.minikube
scp -r david@192.168.0.112:/home/david/.minikube ~/.minikube

sed -i '' 's|/home/david/.minikube|/Users/david/.minikube|g' ~/.kube/config
sed -i '' "s|server: https://127.0.0.1:8443|server: https://ubuntu:8443|" ~/.kube/config
```

Modify in `zshrc` the env variable for the KUBECONFIG.


# Summary

```bash
You are running a full Kubernetes/Argo/MinIO stack on your powerful Ubuntu workstation, while your MacBook acts only as a remote kubectl client. Your previous Minikube installation used the Docker driver, which broke NodePort networking, so we completely removed the old setup and rebuilt Minikube using the none driver, running Kubernetes directly on the host for proper LAN access. Along the way, we fixed missing CNI plugins, created a proper containerd config, resolved Ubuntu’s filesystem protection issue, cleaned out old kube/minikube folders, started Minikube with CHANGE_MINIKUBE_NONE_USER=true so it generates configs for your user, copied root configs to /home/david, rewrote paths inside kubeconfig, corrected permissions, and verified that kubectl now connects to the host-based Minikube cluster successfully.

# Summary of Context and Work Completed

We migrated a Minikube cluster from the Docker driver to the `none` driver on a powerful Ubuntu workstation to enable full host-level networking (especially NodePort access) and to support Argo Workflows, MinIO, and Metaflow without Docker’s network isolation. The client machine is a macOS laptop that only acts as a remote kubectl controller, while the Ubuntu machine runs Kubernetes, containerd, Minikube, and all workloads. Because Minikube with the none driver runs Kubernetes directly on the host, several host-level fixes were required, including installing containerd, CNI plugins, crictl, generating a containerd config, disabling a filesystem protection flag, and fully deleting old kube/minikube directories.

After successfully starting Minikube with the none driver, we resolved kubeconfig issues by copying the kubeconfig and the complete `.minikube` directory (including certificates) from Ubuntu to the Mac, and then fixing Linux paths inside the kubeconfig to align with macOS paths. We also ensured that the Kubernetes API server on Ubuntu was reachable from the Mac (port 8443), and verified that kubectl from macOS could correctly connect to the remote Minikube cluster. The final result is a clean, fully functional Minikube (none driver) cluster accessible remotely from macOS, with proper authentication, networking, and configuration paths.

# IN Mac
echo $UBUNTU_IP
192.168.0.112

cat /etc/hosts

127.0.0.1	localhost
255.255.255.255	broadcasthost
::1             localhost
192.168.0.112  ubuntu

# Final instructions
please from now on be concise and brief on all answers, avoid big dissertations, talk plain english and prioritize showing 1 approach (not many) and do NOT show many steps forward, simply indicate the solution to the errors I show one by one
```



# Concepts

## Why containerd ?
Think of it like this:
- Kubernetes schedules pods
- Kubelet tells containerd to run containers for the pod
- containerd pulls images, creates containers, starts them, stops them
- Kubernetes doesn’t run containers itself — containerd does.

When you use the none driver + containerd:
- Pods run as containerd containers
- They do not use Docker at all.
- They do not run inside docker containers.
- They do not go through Docker networking.