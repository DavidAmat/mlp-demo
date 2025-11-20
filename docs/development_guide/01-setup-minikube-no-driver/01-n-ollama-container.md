# Configure Ollama Container

```bash
# 1) Pull the Ollama Docker image
docker pull ollama/ollama:latest

# 2) Run Ollama in the background on host port 11500
docker run -d \
  --name ollama \
  --gpus all \
  -p 11500:11434 \
  -v ollama:/root/.ollama \
  ollama/ollama:latest

# 3) Pull the model into the container
docker exec -it ollama ollama pull qwen3-coder:latest
```

Test on Ubuntu
```bash
# 4) Test the OpenAI-compatible endpoint
curl http://localhost:11500/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -d '{
    "model": "qwen3-coder:latest",
    "messages": [
      { "role": "user", "content": "Write a simple SQL query to table orders to get from each date the number of order_id. It is PostgreSQL." }
    ]
  }'
```


Test on Mac
```bash
# 4) Test the OpenAI-compatible endpoint
curl http://192.168.0.112:11500/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -d '{
    "model": "qwen3-coder:latest",
    "messages": [
      { "role": "user", "content": "What are the steps to solve a Merge conflict by a git rebase from my local base if master has changed ?" }
    ]
  }'
```

# Stop and resume

```bash
# Stop
docker stop ollama
docker start ollama
```

# Summary

We successfully set up a GPU-accelerated local LLM environment on Ubuntu by running Ollama inside a Docker container configured to use the host’s NVIDIA RTX 4090 through the NVIDIA Container Toolkit. Instead of dealing with complex CUDA, PyTorch, or vLLM compatibility issues, we deployed the official Ollama Docker image, mapped a persistent volume for model storage, exposed the API on a custom port to avoid conflicts with the host’s native Ollama service, and pulled the qwen3-coder model directly inside the container. The container runs continuously in the background and automatically loads the model on demand whenever we send an HTTP request from the Ubuntu host, using either Ollama’s native API or its fully OpenAI-compatible chat completions endpoint. This setup provides a clean, isolated, dependency-free way to run high-performance LLM inference while leveraging the full GPU acceleration of the local machine.