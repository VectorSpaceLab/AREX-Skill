# Local backends, quantization, and VRAM

This is a decision guide for DB-GPT 0.8.1 local model parameters. The route's
required verification is CPU/package/config behavior. Local GPU inference is
optional and must be verified separately with the exact dependency set.

## Hugging Face (`hf`)

Use a local directory or a permitted model identifier:

```toml
[[models.llms]]
name = "local-chat"
provider = "hf"
path = "models/local-chat"
device = "cpu"
trust_remote_code = false
torch_dtype = "float32"
```

Relevant fields:

- `path`: actual local model directory or approved model identifier;
- `device`: explicitly choose `cpu`, `cuda`, or another supported device when
  auto-detection is not safe;
- `trust_remote_code`: enabling it executes model-provided code and requires a
  deliberate trust decision;
- `num_gpus` and `max_gpu_memory`: GPU loading controls;
- `torch_dtype`: `float16`, `bfloat16`, `float`, or `float32` where supported;
- `quantization`: registered bitsandbytes configuration;
- `low_cpu_mem_usage` and attention implementation: optional loading controls.

A missing model path, tokenizer, torch, transformers, or device capability is a
backend failure, not a provider authentication failure.

## vLLM (`vllm`)

vLLM is a local serving backend with GPU-oriented settings:

```toml
[[models.llms]]
name = "local-vllm-chat"
provider = "vllm"
path = "models/local-vllm-chat"
dtype = "auto"
max_model_len = 4096
tensor_parallel_size = 1
gpu_memory_utilization = 0.90
quantization = "${env:VLLM_QUANTIZATION:-}"
```

Important parameters include `dtype`, `kv_cache_dtype`, `max_model_len`,
`tensor_parallel_size`, `pipeline_parallel_size`,
`gpu_memory_utilization`, `swap_space`, `cpu_offload_gb`, `max_num_seqs`,
`max_num_batched_tokens`, `distributed_executor_backend`, and `quantization`.
Choose tensor/pipeline parallel sizes that match the actual device topology.
Increasing `gpu_memory_utilization` does not create VRAM; it can make OOM more
likely. A model that parses with `provider = "vllm"` has not been loaded.

## llama.cpp and llama.cpp server

`llama.cpp` loads a GGUF file in the worker; `llama.cpp.server` manages a child
server process. They are separate provider values:

```toml
[[models.llms]]
name = "gguf-chat"
provider = "llama.cpp"
path = "models/gguf-chat.Q4_K_M.gguf"
ctx_size = 4096
threads = 4
n_gpu_layers = 0

[[models.llms]]
name = "gguf-server-chat"
provider = "llama.cpp.server"
path = "models/gguf-chat.Q4_K_M.gguf"
server_host = "127.0.0.1"
server_port = 0
startup_timeout = 60
n_gpu_layers = 0
```

`n_gpu_layers = 0` is a CPU-oriented choice; a large value requests offload
and needs a backend binary with GPU support. `server_port = 0` can request an
available child port where supported; use a fixed, non-conflicting port when a
network client must connect directly. `server_bin_path` must point to an
executable available in the runtime environment. Do not bundle or run an
opaque compiler/install script from a source repository.

## MLX (`mlx`)

MLX is host-specific and should be selected only on a compatible Apple Silicon
runtime with its dependencies installed. It is not a CPU-equivalent path on a
Linux inspection environment. Keep it explicitly optional.

## Bitsandbytes quantization

DB-GPT exposes bitsandbytes 4-bit and 8-bit parameter families for Hugging Face
loading. The source validation path requires CUDA for these quantization modes:

```toml
[[models.llms]]
name = "quantized-chat"
provider = "hf"
path = "models/quantized-chat"
quantization = { type = "bitsandbytes", load_in_4bits = true }
```

Exact nested syntax is subject to the registered configuration converter; use
its live parameter description/help before relying on a complex table. 4-bit
and 8-bit flags cannot both be enabled. Supported 4-bit compute dtypes are
`bfloat16`, `float16`, and `float32`; quantization type is `nf4` or `fp4`.

Do not infer VRAM fit from parameter count alone. Account for weights, KV
cache, context length, batching, tokenizer/runtime overhead, and any parallel
or offload settings. On OOM, collect device count, free memory, dtype,
quantization, context length, batch/concurrency, and backend version before
changing settings.

## Hardware boundary

The verified environment for this skill is CPU-only. A machine may expose an
NVIDIA GPU while lacking a usable torch/CUDA/vLLM/bitsandbytes stack or a
compiled CUDA llama.cpp binary. Therefore:

- `torch.cuda.is_available()` and a tiny model load are required before claiming
  CUDA support;
- a successful TOML parse/import is never CUDA evidence;
- host driver output alone is not a backend test;
- local model downloads, GPU kernels, and long-running inference are optional
  operations and require explicit runtime/budget approval;
- when the backend is unavailable, recommend a proxy or CPU-compatible smoke,
  but label the original local-GPU path unverified rather than silently
  substituting it.
