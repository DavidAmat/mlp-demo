# Persistent MinIO content

When we launch the Minikube cluster with `make up` in `cluster` folder in Ubuntu, the MinIO service gets up and running from scratch every time.

This means that even if I had created a `metaflow` folder, this won't persist upon restarts

## Create persistent storage on ubuntu

Create the files

- `minio-pv.yaml`
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: minio-pv
spec:
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  storageClassName: manual
  hostPath:
    path: /home/david/cluster/minio
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-pvc
  namespace: argo
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: manual
  resources:
    requests:
      storage: 20Gi
```
- `minio-deployment-persistent.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: argo
  labels:
    app: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      automountServiceAccountToken: false
      containers:
      - name: main
        image: quay.io/minio/minio:latest
        imagePullPolicy: IfNotPresent
        command:
        - minio
        - server
        - --console-address
        - :9001
        - --compat
        - /data
        env:
        - name: MINIO_ACCESS_KEY
          value: admin
        - name: MINIO_SECRET_KEY
          value: password
        ports:
        - containerPort: 9000
          name: api
        - containerPort: 9001
          name: dashboard
        volumeMounts:
        - name: minio-storage
          mountPath: /data
        lifecycle:
          postStart:
            exec:
              command:
              - mkdir
              - -p
              - /data/my-bucket
        livenessProbe:
          httpGet:
            path: /minio/health/live
            port: 9000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /minio/health/ready
            port: 9000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: minio-storage
        persistentVolumeClaim:
          claimName: minio-pvc
```

```bash
# -------------------------------------------
# Create persistent MinIO storage directory
# -------------------------------------------
mkdir -p /home/david/cluster/minio
chmod 755 /home/david/cluster/minio

# -------------------------------------------
# Delete old PV/PVC (if they exist)
# -------------------------------------------
kubectl -n argo delete pvc minio-pvc --ignore-not-found
kubectl delete pv minio-pv --ignore-not-found

# -------------------------------------------
# Apply correct PV + PVC for MinIO
# -------------------------------------------
kubectl apply -f minio-pv.yaml

# -------------------------------------------
# Apply the persistent MinIO Deployment
# -------------------------------------------
kubectl apply -f minio-deployment-persistent.yaml

# -------------------------------------------
# Restart MinIO pod to attach the PVC
# -------------------------------------------
kubectl -n argo delete pod -l app=minio

# -------------------------------------------
# Verify PVC is bound and MinIO is running
# -------------------------------------------
kubectl -n argo get pvc
kubectl -n argo get pods -l app=minio

```

## Test it 

```bash
# -------------------------------------------
# Upload a test file to MinIO
# -------------------------------------------
echo "hello world" > test.txt
AWS_ACCESS_KEY_ID=admin AWS_SECRET_ACCESS_KEY=password \
aws --endpoint-url http://192.168.0.112:32046 s3 cp test.txt s3://my-bucket/

# -------------------------------------------
# List contents before reboot
# -------------------------------------------
AWS_ACCESS_KEY_ID=admin AWS_SECRET_ACCESS_KEY=password \
aws --endpoint-url http://192.168.0.112:32046 s3 ls s3://my-bucket/

# -------------------------------------------
# Reboot Ubuntu
# -------------------------------------------
sudo reboot
```

Then

```bash
# -------------------------------------------
#  Ubuntu restart minikube
# -------------------------------------------
cluster
make up

# -------------------------------------------
# Verify MinIO pod is running
# -------------------------------------------
kubectl -n argo get pods -l app=minio

# -------------------------------------------
# List contents after reboot (persistence test)
# -------------------------------------------
AWS_ACCESS_KEY_ID=admin AWS_SECRET_ACCESS_KEY=password \
aws --endpoint-url http://192.168.0.112:32046 s3 ls s3://my-bucket/
```