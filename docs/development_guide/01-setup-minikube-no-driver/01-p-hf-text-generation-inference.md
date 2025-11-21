# Hugging Face TGI

TGI offers an image to deploy a model from Hugging Face locally.


## Configur Hugging Face


### Install venv

```bash
python3 -m venv .venv\n
source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124\n
pip install transformers accelerate sentencepiece\n
pip install jupyter ipykernel
python -m ipykernel install --user --name kr_hf_llama --display-name "kr_hf_llama"

```

### Install xet and lfs

```python
brew tap huggingface/tap\n
brew install git-xet\n
git xet install\n\n
git xet uninstall
git lfs install
```

We will only need `lfs` to clone

### Prepare SSH key

```python
ssh-keygen -t ed25519 -C "daolondrizdaolondriz@gmail.com"
/home/david/.ssh/id_hf_ubuntu
cat ~/.ssh/id_hf_ubuntu.pub
# copy and paste
nano ~/.ssh/config
Host hf.co
    HostName hf.co
    User git
    IdentityFile ~/.ssh/id_hf_ubuntu
    IdentitiesOnly yes
    
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_hf_ubuntu
ssh -T git@hf.co
```

### Clone

Go to main repo page: [https://huggingface.co/meta-llama/Llama-3.2-1B/tree/main](https://huggingface.co/meta-llama/Llama-3.2-1B/tree/main) and click on 3 dots + Clone repository

```python
git clone git@hf.co:meta-llama/Llama-3.2-1B
# or
hf auth login
hf download meta-llama/Llama-3.2-1B
```

### Notebook

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

torch.cuda.is_available()

local_path = "/mnt/ssd2/hf/Llama-3.2-1B"

tokenizer = AutoTokenizer.from_pretrained(local_path)

model = AutoModelForCausalLM.from_pretrained(
    local_path,
    dtype=torch.bfloat16,   # explícito, NO deprecated
    device_map="auto"
)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)

print(pipe("The capital of France is"))
```

# TGI

We will now deploy a server locally using the TGI docker image and will have a client in python

## Server

```bash
# UBUNTU
docker run --gpus all --shm-size 1g -p 8080:80 \
  -v /mnt/ssd2/hf/Llama-3.2-3B-Instruct:/data \
  ghcr.io/huggingface/text-generation-inference:2.4.0 \
  --model-id /data
```

Ping it locally in Ubuntu and Mac
```bash
# UBUNTU
curl http://localhost:8080/health
curl http://localhost:8080/info

# Trigger completion
curl http://localhost:8080/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "model": "local",
        "messages": [
          {"role": "user", "content": "Who is the singer of Mr Blue Sky song ?"}
        ],
        "max_tokens": 100
      }'

# MAC
curl http://http://192.168.0.112/:8080/health
curl http://192.168.0.112:8080/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "model": "local",
        "messages": [
          {"role": "user", "content": "Who is the singer of Mr Blue Sky song ?"}
        ],
        "max_tokens": 100
      }'
```


## Client

In Python we have created in Ubuntu
```python
# Path: /home/david/Documents/dev/notebooks/hf/llama
# Notebook: client-server-32-3b-instruct.ipynb
# Source: .venv/bin/active
# Huggingface hub is required by accelerate, tokenizers, transformers
from huggingface_hub import InferenceClient
client = InferenceClient("http://localhost:8080")
response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Who is the singer of Mr Blue Sky song ?"}
    ],
    max_tokens=200,
    temperature=0,
    top_p=1e-9,
    seed=0
)
print(response.choices[0].message["content"])

```
