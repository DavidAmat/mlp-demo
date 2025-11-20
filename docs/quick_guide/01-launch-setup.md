# Launch Set Up

In Ubuntu make sure the minikube cluster is running
```bash
minikube start --driver=docker --insecure-registry="192.168.0.112:5000"
minikube status
```

In Mac run in a separate terminal:
```bash
tunnel
```

In Mac check the running pods:
```bash
kgno
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   14h   v1.34.0
```

# Tunnel Network traffic to K8s services to Mac

From my Mac I want to access and do requests to pods and services on my Ubuntu.
I have set up a key-based authentication to allow running in the background the tunnel

```bash
# UBUNTU
#sudo -E minikube tunnel --bind-address 0.0.0.0
tunnel
# run: check_tunnels (defined in zshrc)

# MAC (to be able to reach the K8s API from Mac)
tunnel
# run: check_tunnels (defined in zshrc)
# ssh -f -N -L 8443:192.168.49.2:8443 ubuntu
```

# Launch fastapi demo

```bash
cd demo/
cd fastapi-demo/
k apply -f fastapi-demo.yaml
curl -X POST http://ubuntu:8080/add \
  -H "Content-Type: application/json" \
  -d '{"x": 3, "y": 4}'
```
