# Installing NVIDIA to allow pods use the GPU


## Ubuntu

```bash
# If you don't have installed NVIDIA drivers yet
sudo ubuntu-drivers autoinstall
sudo reboot
# nvidia-smi

```

Configure `containerd` for NVIDIA runtime
```bash
sudo nvidia-ctk runtime configure --runtime=containerd

sudo mkdir -p /etc/containerd/config.d
sudo chmod 666 /etc/containerd/config.d/99-nvidia.toml
```

You should have a file `99-nvidia.tom` with (see Appendix A)

Edit `containerd` to use NVIDIA as the default runtime
```bash
sudo nano /etc/containerd/config.toml

# Change this line
default_runtime_name = "runc"

# To this line
default_runtime_name = "nvidia"

# Restart containerd
sudo systemctl restart containerd
```

## Reinstall NVIDIA Kubernetes Device Plugin
```bash
kubectl delete -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
kubectl apply  -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

Verify
```bash
kubectl -n kube-system get pods | grep nvidia
# nvidia-device-plugin-daemonset-ccxvs   1/1     Running   0              8m45s -->
```

Confirm GPU is advertised to K8s:
```bash
kubectl describe node david | grep -i nvidia
# kubectl describe node david | grep -i nvidia
#   nvidia.com/gpu:     1
#   nvidia.com/gpu:     1
#   kube-system                 nvidia-device-plugin-daemonset-ccxvs    0 (0%)        0 (0%)      0 (0%)           0 (0%)         9m21s
#   nvidia.com/gpu     0
```


# Running Hugging Face

Go to `gpu-demo`:
See guide on `POETRY SETUP`:

```bash
docker build --platform linux/amd64 -t 192.168.0.112:5000/metaflow-gpu-demo:latest .

# Tag the image for your registry
# docker tag gpu-inference-demo:latest 192.168.0.112:5000/metaflow-gpu-demo:latest

# Push the new image
docker push 192.168.0.112:5000/metaflow-gpu-demo:latest
```





# Appendix A: 99-nvidia.toml
```bash
version = 3

[plugins]

  [plugins."io.containerd.cri.v1.runtime"]
    cdi_spec_dirs = ["/etc/cdi", "/var/run/cdi"]
    device_ownership_from_security_context = false
    disable_apparmor = false
    disable_hugetlb_controller = true
    disable_proc_mount = false
    drain_exec_sync_io_timeout = "0s"
    enable_cdi = true
    enable_selinux = false
    enable_unprivileged_icmp = true
    ignore_deprecation_warnings = []
    ignore_image_defined_volumes = false
    max_container_log_line_size = 16384
    netns_mounts_under_state_dir = false
    restrict_oom_score_adj = false
    selinux_category_range = 1024
    tolerate_missing_hugetlb_controller = true
    unset_seccomp_profile = ""

    [plugins."io.containerd.cri.v1.runtime".cni]
      bin_dir = ""
      bin_dirs = ["/opt/cni/bin"]
      conf_dir = "/etc/cni/net.d"
      conf_template = ""
      ip_pref = ""
      max_conf_num = 1
      setup_serially = false
      use_internal_loopback = false

    [plugins."io.containerd.cri.v1.runtime".containerd]
      default_runtime_name = "nvidia"
      ignore_blockio_not_enabled_errors = false
      ignore_rdt_not_enabled_errors = false

      [plugins."io.containerd.cri.v1.runtime".containerd.runtimes]

        [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.nvidia]
          base_runtime_spec = ""
          cgroup_writable = false
          cni_conf_dir = ""
          cni_max_conf_num = 0
          container_annotations = []
          io_type = ""
          pod_annotations = []
          privileged_without_host_devices = false
          privileged_without_host_devices_all_devices_allowed = false
          runtime_path = ""
          runtime_type = "io.containerd.runc.v2"
          sandboxer = "podsandbox"
          snapshotter = ""

          [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.nvidia.options]
            BinaryName = "/usr/bin/nvidia-container-runtime"
            CriuImagePath = ""
            CriuWorkPath = ""
            IoGid = 0
            IoUid = 0
            NoNewKeyring = false
            Root = ""
            ShimCgroup = ""

        [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.runc]
          base_runtime_spec = ""
          cgroup_writable = false
          cni_conf_dir = ""
          cni_max_conf_num = 0
          container_annotations = []
          io_type = ""
          pod_annotations = []
          privileged_without_host_devices = false
          privileged_without_host_devices_all_devices_allowed = false
          runtime_path = ""
          runtime_type = "io.containerd.runc.v2"
          sandboxer = "podsandbox"
          snapshotter = ""

          [plugins."io.containerd.cri.v1.runtime".containerd.runtimes.runc.options]
            BinaryName = ""
            CriuImagePath = ""
            CriuWorkPath = ""
            IoGid = 0
            IoUid = 0
            NoNewKeyring = false
            Root = ""
            ShimCgroup = ""
```