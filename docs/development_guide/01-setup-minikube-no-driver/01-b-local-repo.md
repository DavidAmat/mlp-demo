# Create containerd registry config

Tell containerd that localhost:5000 is a trusted local registry:


```bash
sudo mkdir -p /etc/containerd/certs.d/localhost:5000
sudo tee /etc/containerd/certs.d/localhost:5000/hosts.toml <<EOF
server = "http://localhost:5000"

[host."http://localhost:5000"]
  capabilities = ["pull", "resolve"]
EOF

sudo systemctl restart containerd

```

In the YAML manifest for the deployment

```bash
image: localhost:5000/fastapi-demo:latest
imagePullPolicy: IfNotPresent
```

then apply it

# Cheatsheet

```bash
# UBUNTU
curl http://localhost:5000/v2/_catalog
curl http://localhost:5000/v2/fastapi-demo/tags/list

# MAC
curl http://192.168.0.112:5000/v2/_catalog
curl http://192.168.0.112:5000/v2/fastapi-demo/tags/list
```


# Mac Configure Insecure Registries in Colima

```bash
colima stop
colima delete --force

colima start --runtime docker --edit
```

With vim look for `/^docker`:
```bash
# Colima config

cpu: 4
memory: 6
vm-type: vz
network-address: true
runtime: docker

docker:
  insecure-registries:
    - "192.168.0.112:5000"
```


Verify:
```bash
docker info | grep -A3 "Insecure Registries"
docker push 192.168.0.112:5000/metaflow-city-latency:latest
```

Verify the `YAML` file locally:
```bash
cat ~/.colima/default/colima.yaml
```

# Configure Insecure Registries from Ubuntu

Ubuntu `containerd` (which will be the one used by minikube when deploying Argo containers and Metaflow pipelines) WILL NOT pull images over plain HTTP unless explicitly allowed. So minikube is using the host `containerd`and the `kubelet` uses `containerd` to pull images to launch the pods from the local registry so we need to configure insecure registries for ubuntu too:


```bash
sudo apt install mkcert libnss3-tools -y
mkdir -p ~/registry-certs
cd ~/registry-certs


# THEN
mkcert 192.168.0.112

# Created a new local CA 💥
# Note: the local CA is not installed in the system trust store.
# Note: the local CA is not installed in the Firefox and/or Chrome/Chromium trust store.
# Run "mkcert -install" for certificates to be trusted automatically ⚠️

# Created a new certificate valid for the following names 📜
#  - "192.168.0.112"

# The certificate is at "./192.168.0.112.pem" and the key at "./192.168.0.112-key.pem" ✅

# It will expire on 17 February 2028 🗓

cat ~/registry-certs/192.168.0.112.pem
cat ~/registry-certs/192.168.0.112-key.pem

# Stop old registry
docker ps | grep registry
docker stop <container-id>
docker rm <container-id>

# Run https registry
docker run -d \
  --name registry \
  -p 5000:5000 \
  -v ~/registry-certs/192.168.0.112.pem:/certs/domain.crt \
  -v ~/registry-certs/192.168.0.112-key.pem:/certs/domain.key \
  -v registry-data:/var/lib/registry \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  registry:2

# Tell containerd and kubelet to trust the certificate
sudo cp 192.168.0.112.pem /usr/local/share/ca-certificates/192.168.0.112.crt
sudo update-ca-certificates
# Updating certificates in /etc/ssl/certs...
# rehash: warning: skipping ca-certificates.crt, it does not contain exactly one certificate or CRL
# 1 added, 0 removed; done.
# Running hooks in /etc/ca-certificates/update.d...
# Processing triggers for ca-certificates-java (20240118) ...
# Adding debian:192.168.0.112.pem
# done.
# done.

sudo systemctl restart containerd
sudo systemctl restart kubelet
```

### Now in Mac

```bash
brew install mkcert
mkcert -install

# Createa  folder
mkdir -p ~/.docker/certs.d/192.168.0.112:5000/

# UBUNTU
cat 192.168.0.112.pem
# copy

# MAC
# paste on
nano ~/.docker/certs.d/192.168.0.112:5000/ca.crt
```

You can build an image from Mac and push it
```bash
# Go to directory: demo/metaflow-demo
docker build \
    --platform linux/amd64 \
    -t 192.168.0.112:5000/metaflow-city-latency:latest .
```

### Now my Mac needs to trust the mkcert CA that signed the registry

```bash
# UBUNTU
mkcert -CAROOT
# /home/david/.local/share/mkcert
# ls /home/david/.local/share/mkcert
#  rootCA-key.pem   rootCA.pem

# MAC
scp david@ubuntu:/home/david/.local/share/mkcert/rootCA.pem ~/Downloads/
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/Downloads/rootCA.pem
```


Test:
```bash
# UBUNTU
curl https://192.168.0.112:5000/v2/_catalog
curl https://192.168.0.112:5000/v2/metaflow-city-latency/tags/list

# MAC
curl https://192.168.0.112:5000/v2/_catalog
curl https://192.168.0.112:5000/v2/metaflow-city-latency/tags/list
```

Verify kubernetes can now pull the image
```bash
kubectl run test-pull \
  --rm -it \
  --restart=Never \
  --image=192.168.0.112:5000/metaflow-city-latency:latest \
  --command -- /bin/bash
```


# Final Note (for restarting)

When restarting Ubuntu, add in the `Makefile`:

```bash
docker start registry
```

To ensure registry container starts after reboot