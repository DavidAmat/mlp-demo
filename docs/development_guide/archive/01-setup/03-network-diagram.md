# Diagram

```scss
 ┌────────────────┐        ┌─────────────────────┐        ┌────────────────────────────┐        ┌──────────────────────────┐
 │   MacBook M4   │        │     Ubuntu Host     │        │      Minikube (K8s VM)     │        │   FastAPI Pod (Gunicorn)  │
 │                │        │ (192.168.0.112 LAN) │        │  (Docker network: 192.168.49.x) │   │      ContainerPort: 80     │
 │  curl → :8080  │──────▶ │:8080 (tunnel LB)    │──────▶ │ NodePort (auto-assigned)   │──────▶ │  gunicorn listens :80      │
 └────────────────┘        └─────────────────────┘        └────────────────────────────┘        └──────────────────────────┘
```

- Sends an HTTP POST to Ubuntu’s LAN IP, port 8080.
- [UBUNTU] `sudo -E minikube tunnel --bind-address 0.0.0.0`
    - Opens port 8080 (and 80/443 if needed) on your Ubuntu LAN interface.
    - Watches Kubernetes Services of type LoadBalancer.
    - For each, it adds a local route so traffic on that port is forwarded into the Minikube network.
- [UBUNTU][Minikube]
    - Service Port (8080) = external port of the LoadBalancer (this matches what the tunnel exposes)
    - Target Port (80) = where the container in the pod listens (Gunicorn)

# Minikube Tunnel

tunnel creates a route to services deployed with type LoadBalancer and sets their Ingress to their ClusterIP. for a detailed example see https://minikube.sigs.k8s.io/docs/tasks/loadbalancer

`--bind-address string`:  set tunnel bind address, empty or '*' indicates the tunnel should be available for all interfaces