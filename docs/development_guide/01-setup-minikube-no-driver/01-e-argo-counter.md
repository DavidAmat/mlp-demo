
```bash
docker build \
  --platform linux/amd64 \
  -t 192.168.0.112:5000/argo-counter:latest .
docker push 192.168.0.112:5000/argo-counter:latest

curl https://192.168.0.112:5000/v2/argo-counter/tags/list
```

Submit
```bash
argo submit -n argo argo-counter-wf.yaml


# Monitor
kubectl -n argo get wf -w
```