# Poetry Setup Guide for Cross-Platform Dependency Resolution

## The Problem
When you run `poetry lock` or `poetry install` on your Mac (especially Apple Silicon), Poetry resolves dependencies for macOS, which can differ from the Ubuntu + NVIDIA CUDA environment where the code will actually run.

## The Solution
Generate the `poetry.lock` file **inside a Docker container** that matches the production environment (Ubuntu 22.04 + CUDA 11.8).

---

## Step 1: Generate poetry.lock Using Docker

We have a special `Dockerfile.lock-generator` that creates the lock file on the target platform.

### Run this command from the `demo/gpu-demo` directory:

```bash
# Build the lock generator image
docker build -f Dockerfile.lock-generator -t gpu-demo-lock-generator .

# Run the container to generate poetry.lock
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry lock

# Verify the lock file was created
ls -lh poetry.lock
```

**What this does:**
- Creates a container with Ubuntu 22.04 + CUDA 11.8 + Python 3.10
- Installs Poetry inside the container
- Generates `poetry.lock` based on `pyproject.toml` using the Ubuntu platform
- Mounts your current directory so `poetry.lock` is created on your Mac

---

## Step 2: Build the Main Docker Image

Once you have `poetry.lock`, build the main image:

```bash
docker build -t gpu-inference-demo:latest .
```

---

## Step 3: (Optional) Update Dependencies

When you need to update dependencies in the future:

### Option A: Update All Dependencies
```bash
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry update
```

### Option B: Update Specific Package
```bash
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry update transformers
```

### Option C: Add New Dependency
```bash
# First, manually add to pyproject.toml [tool.poetry.dependencies] section
# Then regenerate the lock:
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry lock
```

---

## Why This Approach?

### ✅ Advantages:
1. **Platform-accurate dependencies**: Lock file is generated on the exact target platform
2. **No Mac-specific packages**: Avoids resolving Mac/ARM-specific wheels
3. **Reproducible builds**: Same lock file works across different developer machines
4. **CI/CD friendly**: Can use the same approach in GitHub Actions/CI pipelines
5. **No Poetry installation needed on Mac**: Everything happens in Docker

### ❌ What NOT to do:
```bash
# DON'T run this on your Mac - it will generate Mac-specific dependencies
poetry lock  # ❌ Wrong platform
poetry install  # ❌ Wrong platform
```

---

## Verifying Dependencies

After generating the lock file, you can inspect it:

```bash
# View all locked packages
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry show

# Check if PyTorch has CUDA support
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry show torch

# Export to requirements.txt format (for comparison)
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry export -f requirements.txt
```

---

## Quick Reference Commands

```bash
# Generate/regenerate lock file
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry lock

# Update all dependencies
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry update

# Add a new package
# 1. Edit pyproject.toml manually
# 2. Run:
docker run --rm -v $(pwd):/app gpu-demo-lock-generator poetry lock

# Build the main image
docker build -t gpu-inference-demo:latest .

# Clean up the lock generator image
docker rmi gpu-demo-lock-generator
```

---

## Notes

- The `poetry.lock` file should be committed to version control
- The lock generator image only needs to be rebuilt if you change the base image or Poetry version
- If you're working with other developers, they should use the same lock file generation method
- For CI/CD pipelines, you can use the same Docker-based approach to validate the lock file

