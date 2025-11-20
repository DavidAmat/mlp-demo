# Accessing a running service

- Build container
```bash
docker build --platform linux/amd64 -t 192.168.0.112:5000/fastapi-demo:latest .

```

- Apply the fastapi-demo.yaml

- Check the NodePort:

```bash
kubectl get svc
# fastapi-demo   LoadBalancer   10.103.160.246   <pending>   8080:31178/TCP   1m
```


```bash
# MAC
# Make sure you target the same NodePort 31178 as it appears in the get svc
curl -X POST http://192.168.0.112:31178/add \
  -H "Content-Type: application/json" \
  -d '{"x":3,"y":4}'

# UBUNTU
  curl -X POST http://localhost:31178/add \
  -H "Content-Type: application/json" \
  -d '{"x":3,"y":4}'
```



# Summary


## Minikube (none driver) + Local Registry + Remote Access Setup Summary

We migrated a Minikube cluster running on a powerful Ubuntu workstation from the Docker driver to the **none driver**, allowing Kubernetes to run directly on the host and enabling full LAN-level networking. The goal was to host a local artifact registry on the same Ubuntu machine and deploy workloads (like a FastAPI demo) using images stored in that registry. The macOS laptop acted as a **remote kubectl client**, connecting to the Ubuntu-based cluster over the LAN.

During setup, we reconfigured Kubernetes, containerd, and Minikube to communicate seamlessly. We fixed CNI plugins, containerd configuration, kubeconfig permissions, and cross-machine TLS certificates so that both Ubuntu and macOS clients could authenticate properly. The critical step was teaching containerd to recognize the **local registry (localhost:5000)** as a trusted source by creating a specific `hosts.toml` configuration file under `/etc/containerd/certs.d/localhost:5000/`. This avoided the need for insecure flags and enabled image pulls directly from the host’s registry.

Finally, we deployed the FastAPI demo image to the cluster and exposed it via a Kubernetes Service. Since Minikube with the none driver lacks an external load balancer, access was done using the **NodePort** automatically assigned by Kubernetes. The service became reachable from both Ubuntu and macOS machines via the workstation’s LAN IP and the exposed NodePort, confirming that the setup worked end-to-end with clean, production-grade configuration.
"""
