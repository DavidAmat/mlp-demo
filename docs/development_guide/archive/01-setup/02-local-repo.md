# Demo: Fast API Demo

## Create a container registry locally

In your Ubuntu run:

```bash
docker run -d \
  -p 5000:5000 \
  -v /opt/registry/data:/var/lib/registry \
  --restart=always \
  --name registry \
  registry:2
```

We are setting a volume in `/opt/registry/data` to persist images between restarts.

## Ensure you can reach it

Access an HTTP registry of containers:

- From Ubuntu: `curl http://localhost:5000/v2/_catalog`
- From Mac: `curl http://192.168.0.112:5000/v2/_catalog`
The result should be `{"repositories":[]}`.

## Mark registry to be trusted by Docker over HTTPS

By default, Docker only trusts registries over HTTPS.
Since this is your private LAN, we’ll configure both Docker daemons to allow HTTP.

### On Mac
Since we are using `colima` in our Mac we should configure the `Insecure Registries`:

```bash
code ~/.colima/default/colima.yaml
```

```bash
# Colima default behaviour: buildkit enabled
# Default: {}
docker:
  insecure-registries:
    - "192.168.0.112:5000"
```

Now Colima’s internal Docker daemon (the one your CLI uses) will happily push/pull to your Ubuntu registry.

Restart to apply changes:

```bash
colima stop
colima start
docker info | grep -A3 'Insecure Registries'
```


### On Ubuntu

```bash
# Edit the daemon to include insecure registries
sudo nano /etc/docker/daemon.json

{
    "runtimes": {
        "nvidia": {
            "args": [],
            "path": "nvidia-container-runtime"
        }
    },
    "insecure-registries": [
        "192.168.0.112:5000"
    ]
}

# Restart to apply changes
sudo systemctl restart docker


# Ensure docker restarted
sudo systemctl status docker --no-pager

# Ensure insecure registry is there
docker info | grep -A3 'Insecure Registries'
```


# Install docker buildx on Mac

On your mac run

```bash
brew install docker-buildx
```

Edit your config json for docker

```bash
code ~/.docker/config.json
```

The json should be:

```json
{
	"auths": {},
	"currentContext": "colima",
	"cliPluginsExtraDirs": [
		"/opt/homebrew/lib/docker/cli-plugins"
	]
}
```

Test in new terminal

```bash
docker buildx version
```

Ensure the platform for ubuntu is available
```bash
docker buildx create --name colima-builder --use --driver docker-container
docker buildx inspect --bootstrap
# see the platforms available
docker buildx ls
```

## Build container and push it to Local Registry
```bash
# This image is for the linux minikube cluster
# docker build \
#   --platform linux/amd64 \
#   -t 192.168.0.112:5000/fastapi-demo:latest .

# Build image to test in mac
docker build \
  --platform linux/arm64 \
  -t fastapi-demo:latest .
docker images

# Push only for the linux minikube cluster image to the local repo  
# docker push 192.168.0.112:5000/fastapi-demo:latest
```

Verify for the pushed image to the registry:
```bash
# UBUNTU
curl http://localhost:5000/v2/_catalog
curl http://localhost:5000/v2/fastapi-demo/tags/list

# Verify inside minikube
minikube ssh # UBUNTU
docker pull 192.168.0.112:5000/fastapi-demo:latest
```



## Run container

In your Mac ensure the container works ok:
```bash
# docker run -d -p 8080:80 192.168.0.112:5000/fastapi-demo:latest
docker run -d -p 8080:80 fastapi-demo:latest
```

In a terminal run:
```bash
curl -X POST http://localhost:8080/add \
  -H "Content-Type: application/json" \
  -d '{"x": 5, "y": 3}'
```

Inspect the logs for the container (see `docker ps` the container id):
```bash
docker logs 0ff40e1535b0 -f
```

Stop:
```bash
docker stop 0ff40e1535b0
```

## Tag and push to the local Ubuntu registry

Esnure the image is properly tagged with the local registry
```bash
# docker tag fastapi-demo:latest 192.168.0.112:5000/fastapi-demo:latest

docker images
# REPOSITORY                        TAG         IMAGE ID       CREATED         SIZE
# fastapi-demo                      latest      f890f63f841c   3 minutes ago   252MB
# 192.168.0.112:5000/fastapi-demo   latest      f890f63f841c   3 minutes ago   252MB

docker push 192.168.0.112:5000/fastapi-demo:latest
```

When you push you should be able to see the catalog of local images from Mac and Ubuntu (remember the local registry is in `/opt/registry/data`, see `/opt/registry/data/docker/registry/v2/repositories` a new directory for `fastapi-demo`)

```bash
# UBUNTU
curl http://localhost:5000/v2/_catalog
curl http://localhost:5000/v2/fastapi-demo/tags/list

# MAC
curl http://192.168.0.112:5000/v2/_catalog
curl http://192.168.0.112:5000/v2/fastapi-demo/tags/list

```

Perfect — your image is now visible to Ubuntu and Minikube.

# Launching Service to Kubernetes

Simply create a new deployment and a new service in `fastapi-demo.yaml`.

Apply it to the cluster using your Mac
```bash
k apply -f fastapi-demo.yaml
kubectl get pods -l app=fastapi-demo
kubectl get svc fastapi-demo
```

Test it from the Mac
```bash
curl -X POST http://192.168.0.112:8080/add \
  -H "Content-Type: application/json" \
  -d '{"x": 3, "y": 4}'
  # OR
curl -X POST http://ubuntu:8080/add \
  -H "Content-Type: application/json" \
  -d '{"x": 3, "y": 4}'
```

# Configure Hosts

```bash
sudo nano /etc/hosts

# add:     192.168.0.112  ubuntu

curl -X POST http://127.0.0.1:8080/add \
  -H "Content-Type: application/json" \
  -d '{"x": 3, "y": 4}'
```