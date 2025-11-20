# Basics

## Remove all Succeeded and Failed Pods
From a given namespace `argo`:
```bash
kubectl delete pod -n argo --field-selector=status.phase==Succeeded
kubectl delete pod -n argo --field-selector=status.phase==Failed
```