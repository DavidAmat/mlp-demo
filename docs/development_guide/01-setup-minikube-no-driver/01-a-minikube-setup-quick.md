# Quick Guide

## START

```bash
# Start
sudo systemctl start containerd
sudo CHANGE_MINIKUBE_NONE_USER=true minikube start --driver=none --container-runtime=containerd
```

### Automating start

We have created `cluster` folder so go and run

```bash
# UBUNTU
cluster
make up


# Makefile
.PHONY: up down status

up:
	sudo systemctl start containerd
	sudo -E env CHANGE_MINIKUBE_NONE_USER=true minikube start --driver=none --container-runtime=containerd

down:
	sudo systemctl stop kubelet
	sudo systemctl stop containerd

status:
	minikube status

ports:
	@ports="8443 10259 10257"; \
	for p in $$ports; do \
		echo -n "Checking port $$p... "; \
		if ss -ltn | grep -q ":$$p "; then \
			echo "IN USE"; \
		else \
			echo "FREE"; \
		fi \
	done
```


## STOP



```bash
# Stop
sudo systemctl stop kubelet
sudo systemctl stop containerd
```