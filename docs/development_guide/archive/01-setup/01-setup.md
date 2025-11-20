# Set Up

## Install Minikube on Ubuntu


```bash
# minikube start --driver=docker --memory=16384 --cpus=8
minikube start --driver=docker \
  --insecure-registry="192.168.0.112:5000"
```

### Minikube status

```bash
minikube status
kubectl get nodes
kubectl get pods -A
```

Configure contexts


```bash
kubectl config get-contexts

# CURRENT   NAME         CLUSTER      AUTHINFO                               NAMESPACE
#           cluster-ai   cluster-ai   clusterUser_rg-cluster-ai_cluster-ai
# *         minikube     minikube     minikube                               default
```

Switch context;

```bash
kubectl config use-context minikube
```

### Verify it works


```bash
kubectl create deployment nginx-demo --image=nginx:alpine

kubectl expose deployment nginx-demo --type=NodePort --port=80

kubectl get svc nginx-demo

# Get the minikube IP
minikube ip


# From Ubuntu ensure we get the html of nginx
curl http://192.168.49.2:31304

# URL
minikube service nginx-demo --url

```

## Tunnelling from Ubuntu to my Mac

[Ubuntu] Make sure the service type is LoadBalancer
```bash
# 1) Change the Service type
kubectl patch svc nginx-demo -p '{"spec":{"type":"LoadBalancer"}}'

# 2) Keep this open
kubectl get svc nginx-demo -w
```

[Ubuntu] Then open a new terminal in Ubuntu
It will create routes and open port 80 (and 443 if needed) on Ubuntu’s LAN IP (192.168.0.112).
This tunnel exposes LoadBalancer-type Services from inside the Minikube cluster to the Ubuntu host’s network interface (your LAN).
When you create a Service of type LoadBalancer in Minikube, Kubernetes marks it as “pending external IP.”
```bash
# keep this running in its own terminal
sudo -E minikube tunnel --bind-address 0.0.0.0
```
Running minikube tunnel creates:
- A network bridge + routes that forward real host ports (like 80, 443, etc.) on Ubuntu → to the service’s internal ClusterIP or NodePort inside Minikube.
- With --bind-address 0.0.0.0, those ports listen on all network interfaces, meaning any device on your LAN (like your Mac) can reach them via Ubuntu’s IP (e.g. 192.168.0.112).

We should now see:
```bash
kubectl get svc nginx-demo
# NAME         TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
# nginx-demo   LoadBalancer   10.107.171.181   127.0.0.1     80:31304/TCP   11m
```

[Mac] Then you can access `http://192.168.0.112:80` the nginx service
or you can `curl -I http://192.168.0.112` in the Mac terminal



## Managing Cluster from Mac

### Install kubectl in Mac
```bash
brew install kubectl
```


### Obtain the kubeconfig from the Ubuntu machine

On the Ubuntu machine, Minikube will have created a kubeconfig (usually at ~/.kube/config for the david user). You need to copy this to the Mac and make sure it can reach the API server.

```bash
# UBUNTU
grep server ~/.kube/config
# server: https://cluster-ai-iallugha.hcp.eastus.azmk8s.io:443
# server: https://192.168.49.2:8443 <- this is the one
```

Run this tunnel in your Mac (keep it open).
This tunnel forwards port 8443 on your Mac (127.0.0.1:8443) → to port 8443 inside Ubuntu’s Docker network, where the Kubernetes API server (Minikube’s control plane) is actually listening.
- When you start Minikube with the Docker driver, the API server is running inside a Docker container with a private IP (e.g., 192.168.49.2).
- That IP (192.168.49.2) only exists inside Ubuntu’s Docker network — your Mac cannot see it directly.
- By creating this SSH tunnel:
    - The Mac connects over SSH to Ubuntu (192.168.0.112, which is reachable).
    - SSH then forwards any traffic sent to 127.0.0.1:8443 on the Mac → 192.168.49.2:8443 inside Ubuntu’s private network.
The syntax is `-L [bind_address:]port:host:hostport`. So if you don’t specify a bind_address, SSH implicitly defaults to 127.0.0.1.
```bash
# MAC
ssh -N -L 8443:192.168.49.2:8443 david@192.168.0.112
```

Acces from your Mac to the URL
```bash
https://127.0.0.1:8443/
# {
#   "kind": "Status",
#   "apiVersion": "v1",
#   "metadata": {},
#   "status": "Failure",
#   "message": "forbidden: User \"system:anonymous\" cannot get path \"/\"",
#   "reason": "Forbidden",
#   "details": {},
#   "code": 403
# }
```

That 403 Forbidden from the Kubernetes API confirms your Mac now has a working network path to the Ubuntu-hosted Minikube API server. It’s rejecting you only because you’re unauthenticated — meaning the connection is alive and the certificates will fix the 403 next.

### Adjust Kubeconfig

Now we’ll make your Mac’s kubectl use the correct credentials and API address.

```bash
# UBUNTU
kubectl config view --minify --flatten --context=minikube > ~/remote-minikube.yaml

# COPY from UBUNTU to MAC
scp david@192.168.0.112:/home/david/remote-minikube.yaml remote-minikube.yaml

# Then modify the yaml file:
# [REPLACE]
server: https://192.168.49.2:8443

# [TO]
server: https://127.0.0.1:8443
# (That matches your SSH tunnel.)
```

Configure you `.zshrc` file to:
```bash
export KUBECONFIG="/Users/david/Documents/projects/backend/youtube-audio-converter/backend-microservices-converters/minikube/remote-minikube.yaml"
alias tunnel="ssh -N -L 8443:192.168.49.2:8443 david@192.168.0.112"
```

```bash
XXX
```

```bash
XXX
```

# Set Up kubectl aliases

```bash
curl -sL https://raw.githubusercontent.com/ahmetb/kubectl-aliases/master/.kubectl_aliases -o ~/.kubectl_aliases
# Add to zshrc file:
source ~/.kubectl_aliases
```

# Install k9s

```bash
brew install derailed/k9s/k9s
```