# Qwen Model Family and Backend Overview

Read this before choosing a checkpoint, precision, backend, or workflow.

## Model choice

- `Qwen/Qwen-7B`, `Qwen/Qwen-14B`, and related `Qwen-*` names are base language models for continuation and scoring-style prompts.
- `Qwen/Qwen-7B-Chat`, `Qwen/Qwen-14B-Chat`, `Qwen/Qwen-1_8B-Chat`, and `Qwen/Qwen-72B-Chat` are aligned chat checkpoints exposing Qwen-specific `chat` and `chat_stream` behavior through remote model code.
- ModelScope names use the lowercase namespace, for example `qwen/Qwen-7B-Chat`; cloud DashScope names such as `qwen-turbo` are hosted service identifiers and are not local checkpoint directories.
- Quantized names such as `Qwen/Qwen-7B-Chat-Int4` are not interchangeable with BF16 checkpoints for Q-LoRA. Use the exact model family expected by the workflow.

## Compatibility baseline

The repository documents Python 3.8+, PyTorch 1.12+ with 2.x recommended, Transformers 4.32+ (4.32.0 preferred in the FAQ), and CUDA 11.4+ recommended for GPU users. The repository requirement file constrains Transformers to `<4.38.0` and includes Accelerate, tiktoken, einops, `transformers_stream_generator==0.0.4`, and SciPy.

FlashAttention is optional. It can reduce memory/useful latency on supported NVIDIA generations, but the models should remain usable without it. Do not install it before matching the PyTorch/CUDA/Python ABI and GPU compute capability.

## Precision and memory decisions

- `device_map="auto"` is the normal multi-device loading path; use `device_map="cpu"` only when slow CPU inference is acceptable.
- BF16 is preferred by the repository for compatible training and inference hardware. FP16 is used for many Int4/Q-LoRA paths and older GPUs.
- Multiple-GPU loading through the native Transformers path is easy but may have low pipeline efficiency; vLLM with tensor parallelism is the preferred deployment path when serving throughput matters.
- The published performance tables are historical A100 measurements, not capacity guarantees. Treat model size, sequence length, batch size, KV cache, and quantization as a combined memory budget.
- Int4/Int8 AutoGPTQ wheels are tightly coupled to the PyTorch, CUDA, Transformers, Optimum, PEFT, and GPU versions. Pin a compatible matrix before installing.

## Context and tokenizer implications

Qwen's historical long-context behavior depends on checkpoint configuration such as dynamic NTK, LogN attention, window attention, and model-specific context limits. Do not promise a context length merely from a prompt length; inspect the loaded generation/config metadata.

The tokenizer uses byte-level BPE plus special/control tokens. Qwen ChatML uses `<|im_start|>` and `<|im_end|>`; the base model mainly uses `<|endoftext|>`. Padding is a workflow-specific choice, not a conventional BOS/EOS contract. Read `sub-skills/prompting-tool-use-tokenization/references/tokenization-and-chatml.md` before adding tokens or changing padding.

## Backend matrix

| Workflow | Base dependency | Typical extra/backend | What a CPU check proves |
| --- | --- | --- | --- |
| Transformers import and command planning | `requirements.txt` | optional torch CUDA/FlashAttention | imports and parser/data guidance only |
| Local generation | Transformers + torch + checkpoint | CUDA recommended; CPU possible but slow | no actual model generation without a checkpoint |
| vLLM/FastChat serving | vLLM, FastChat, compatible torch/CUDA | CUDA and model-compatible wheel | no service/runtime proof |
| Full/LoRA/Q-LoRA training | torch, Transformers, PEFT, DeepSpeed/AutoGPTQ | CUDA, VRAM, distributed runtime | data validation and command planning only |
| GPTQ quantization | AutoGPTQ + Optimum + calibration data | compatible CUDA wheel | parser/data checks only |
| Docker deployment | Docker + NVIDIA Container Toolkit | Qwen image and checkpoint | command syntax only |
| DashScope | cloud SDK/service and API key | network and credentials | nothing about the cloud service |
| Ascend/DCU | vendor runtime and device mounts | vendor image/toolkit | no portable CPU substitute |
