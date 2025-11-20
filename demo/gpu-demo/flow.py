import json
import os
import time

from metaflow import FlowSpec, environment, resources, step

# Shared environment variables for all steps
COMMON_ENV = {
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    "AWS_DEFAULT_REGION": "us-east-1",
    "NVIDIA_VISIBLE_DEVICES": "all",
}


class GPUInferenceFlow(FlowSpec):
    """
    A Metaflow workflow that tests GPU availability and runs
    Hugging Face model inference on a GPU-enabled Kubernetes pod.
    """

    @environment(vars=COMMON_ENV)
    @resources(cpu=1, memory=2048)
    @step
    def start(self):
        """
        Starting step - prints configuration and environment info.
        """
        print("=" * 60)
        print("GPU Inference Flow - Starting")
        print("=" * 60)
        print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')}")
        print(f"AWS_SECRET_ACCESS_KEY: {os.getenv('AWS_SECRET_ACCESS_KEY')}")
        print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION')}")

        self.test_prompt = "Explain what an LLM is"
        print(f"\nTest prompt: {self.test_prompt}")

        self.next(self.check_gpu)

    @environment(vars=COMMON_ENV)
    @resources(cpu=2, memory=8192, gpu=1)
    @step
    def check_gpu(self):
        """
        Check GPU availability and print diagnostic information.
        """
        print("\n" + "=" * 60)
        print("GPU Availability Check")
        print("=" * 60)

        import subprocess
        import sys

        # Print Python and system info
        print(f"Python version: {sys.version}")
        print(f"Python executable: {sys.executable}")

        # Check for nvidia-smi
        print("\n--- Checking nvidia-smi ---")
        try:
            result = subprocess.run(
                ["nvidia-smi"], capture_output=True, text=True, timeout=10
            )
            print("nvidia-smi output:")
            print(result.stdout)
            if result.stderr:
                print("nvidia-smi stderr:")
                print(result.stderr)
            self.nvidia_smi_available = True
        except FileNotFoundError:
            print("nvidia-smi not found in PATH")
            self.nvidia_smi_available = False
        except Exception as e:
            print(f"Error running nvidia-smi: {e}")
            self.nvidia_smi_available = False

        # Check PyTorch CUDA availability
        print("\n--- Checking PyTorch CUDA ---")
        try:
            import torch

            print(f"PyTorch version: {torch.__version__}")
            print(f"CUDA available: {torch.cuda.is_available()}")

            if torch.cuda.is_available():
                print(f"CUDA version: {torch.version.cuda}")
                print(f"Number of GPUs: {torch.cuda.device_count()}")
                for i in range(torch.cuda.device_count()):
                    print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
                    print(
                        f"    Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB"
                    )

                self.cuda_available = True
                self.gpu_count = torch.cuda.device_count()
                self.gpu_name = (
                    torch.cuda.get_device_name(0)
                    if torch.cuda.device_count() > 0
                    else "N/A"
                )

                # Allocate a big tensor (~1GB)
                print("Allocating a big tensor (~1GB)...")
                tensor = torch.randn(1024, 1024, 1024).to(torch.cuda.current_device())
                print("Tensor allocated on GPU:", tensor.device)
                print(
                    "GPU mem (alloc/rsrv):",
                    torch.cuda.memory_allocated() / 1e9,
                    torch.cuda.memory_reserved() / 1e9,
                )
                del tensor
                torch.cuda.empty_cache()
                print(
                    "GPU mem (alloc/rsrv) after empty_cache:",
                    torch.cuda.memory_allocated() / 1e9,
                    torch.cuda.memory_reserved() / 1e9,
                )
            else:
                print("PyTorch CUDA not available")
                print("Possible reasons:")
                print("  - No GPU device found")
                print("  - CUDA drivers not installed")
                print("  - PyTorch not compiled with CUDA support")
                self.cuda_available = False
                self.gpu_count = 0
                self.gpu_name = "N/A"

        except ImportError as e:
            print(f"PyTorch import error: {e}")
            self.cuda_available = False
            self.gpu_count = 0
            self.gpu_name = "N/A"
        except Exception as e:
            print(f"Error checking PyTorch CUDA: {e}")
            self.cuda_available = False
            self.gpu_count = 0
            self.gpu_name = "N/A"

        # Check environment variables
        print("\n--- Environment Variables ---")
        cuda_vars = [
            "CUDA_VISIBLE_DEVICES",
            "NVIDIA_VISIBLE_DEVICES",
            "LD_LIBRARY_PATH",
        ]
        for var in cuda_vars:
            value = os.getenv(var, "Not set")
            print(f"{var}: {value}")

        self.next(self.run_inference)

    @environment(vars=COMMON_ENV)
    @resources(cpu=2, memory=8192, gpu=1)
    @step
    def run_inference(self):
        """
        Run Hugging Face model inference using Qwen3Guard-Gen-8B for safety moderation.
        """
        print("\n" + "=" * 60)
        print("Running Hugging Face Inference")
        print("=" * 60)

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # Determine device
        device_name = "GPU" if torch.cuda.is_available() else "CPU"

        print(f"\nUsing device: {device_name}")
        print(f"Prompt: {self.test_prompt}")

        # Load model and run inference
        model_name = "Qwen/Qwen3Guard-Gen-8B"
        print(f"\nLoading model ({model_name})...")
        start_load = time.time()

        try:
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            # model = AutoModelForCausalLM.from_pretrained(
            #     model_name, torch_dtype="auto", device_map="auto"
            # )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.bfloat16,  # or torch.float16
                device_map="cuda",  # force full model to cuda:0
                low_cpu_mem_usage=True,
            )
            print("Param device:", next(model.parameters()).device)
            print("Device map:", getattr(model, "hf_device_map", None))
            print(
                "GPU mem (alloc/rsrv):",
                torch.cuda.memory_allocated() / 1e9,
                torch.cuda.memory_reserved() / 1e9,
            )

            load_time = time.time() - start_load
            print(f"Model loaded in {load_time:.2f} seconds")

            print("\nRunning inference...")
            start_inference = time.time()

            # Prepare the model input for prompt moderation
            messages = [{"role": "user", "content": self.test_prompt}]

            # Apply chat template
            text = tokenizer.apply_chat_template(messages, tokenize=False)

            # Tokenize input
            model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

            # Generate response
            generated_ids = model.generate(**model_inputs, max_new_tokens=128)

            # Decode only the generated part (exclude input)
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()
            generated_text = tokenizer.decode(output_ids, skip_special_tokens=True)

            inference_time = time.time() - start_inference
            print(f"Inference completed in {inference_time:.2f} seconds")

            print("\n" + "-" * 60)
            print("Generated Text:")
            print("-" * 60)
            print(generated_text)
            print("-" * 60)

            # Store results
            self.inference_result = {
                "prompt": self.test_prompt,
                "generated_text": generated_text,
                "device": device_name,
                "load_time_seconds": round(load_time, 2),
                "inference_time_seconds": round(inference_time, 2),
                "model": model_name,
            }
            self.inference_successful = True

        except Exception as e:
            print(f"\nError during inference: {e}")
            import traceback

            traceback.print_exc()

            self.inference_result = {"error": str(e), "device": device_name}
            self.inference_successful = False

        self.next(self.end)

    @environment(vars=COMMON_ENV)
    @resources(cpu=1, memory=2048)
    @step
    def end(self):
        """
        Final step - aggregate results and save to S3.
        """
        print("\n" + "=" * 60)
        print("GPU Inference Flow - Summary")
        print("=" * 60)

        summary = {
            "gpu_check": {
                "nvidia_smi_available": self.nvidia_smi_available,
                "cuda_available": self.cuda_available,
                "gpu_count": self.gpu_count,
                "gpu_name": self.gpu_name,
            },
            "inference": self.inference_result,
            "inference_successful": self.inference_successful,
        }

        print("\nFinal Summary:")
        print(json.dumps(summary, indent=2))

        # Save to local file
        with open("gpu_inference_results.json", "w") as f:
            json.dump(summary, f, indent=2)
        print("\nWrote gpu_inference_results.json")

        # Upload to MinIO
        try:
            import boto3

            endpoint_url = os.getenv("METAFLOW_S3_ENDPOINT_URL")
            print(f"\nUploading results to MinIO at {endpoint_url}")

            s3 = boto3.client("s3", endpoint_url=endpoint_url)
            s3.upload_file(
                "gpu_inference_results.json",
                "metaflow",
                "gpu-inference-demo/gpu_inference_results.json",
            )
            print("Upload successful!")

        except Exception as e:
            print(f"Error uploading to S3: {e}")

        print("\n" + "=" * 60)
        print("Flow completed!")
        print("=" * 60)


if __name__ == "__main__":
    GPUInferenceFlow()
