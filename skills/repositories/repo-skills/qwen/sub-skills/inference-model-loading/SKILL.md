---
name: inference-model-loading
description: "Route Qwen model loading, local or cloud inference, batch
  generation, backend choice, precision, quantized checkpoints, and long-context
  planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qwen Inference and Model Loading

Use this sub-skill when the user wants to load a Qwen checkpoint, run chat or text generation, choose a model/backend, plan batch inference, diagnose local checkpoint loading, or decide between Transformers, ModelScope, DashScope, CPU, CUDA, quantized, and long-context paths.

## First decisions

1. Identify the model family: base `Qwen-*` for continuation/generation, or `Qwen-*-Chat` for `chat`/`chat_stream` and multi-turn assistant behavior.
2. Identify where the checkpoint comes from: Hugging Face model id, ModelScope id, DashScope hosted API, or an already-downloaded local directory.
3. Identify runtime limits: CPU-only, single CUDA GPU, multiple GPUs, vLLM serving, no network, no credentials, or no checkpoint yet.
4. Run the safe checklist before model loading when the user is debugging setup:
   ```bash
   python scripts/qwen_inference_checklist.py --model Qwen/Qwen-7B-Chat --backend auto --precision auto
   ```

## Routes

| User request | Read |
| --- | --- |
| Basic Transformers or ModelScope loading, local checkpoint fallback, `model.chat`, `model.generate`, history, or no-network setup | `references/model-loading-and-inference.md` |
| Model sizes, base vs chat choice, CPU/CUDA/DashScope/vLLM backend, precision, quantization, KV cache, or long-context tradeoffs | `references/model-and-backend-matrix.md` |
| Batch inference, ChatML stop words, vLLM transformer-like wrapper behavior, or when to route service launch elsewhere | `references/vllm-and-batch-inference.md` |
| Errors about missing tokenizer files, remote code, slow CPU, bad generations, optional dependencies, quantization, or memory | `references/troubleshooting.md` |

## Boundaries

- For CLI, web UI, OpenAI-compatible API, Docker, vLLM/FastChat service launch, TensorRT, Ascend, or DCU deployment, use `../serving-deployment/SKILL.md`.
- For fine-tuning, LoRA, Q-LoRA, adapter merge, or creating GPTQ checkpoints, use `../finetuning-quantization/SKILL.md`.
- For ReAct prompts, function-calling schemas, ChatML internals, tokenizer special tokens, or BPE merge extension, use `../prompting-tool-use-tokenization/SKILL.md`.
- For benchmark reproduction, use `../evaluation-reproduction/SKILL.md`.

## Operating rules

- Keep `trust_remote_code=True` visible for historical Qwen checkpoints. Remote code means code from the checkpoint is executed locally; use a trusted checkpoint source.
- Do not load a remote model as a smoke test unless the user accepts network, storage, and model-code execution. A dependency import check is safer.
- Do not present CPU as a performance equivalent to CUDA; CPU-only loading is mainly for compatibility or very small/debug runs.
- Do not infer that quantized, vLLM, FlashAttention, or KV-cache behavior is verified from a base Transformers import.
- When the user has a local checkpoint, validate `config.json`, tokenizer assets, and model shards before changing Python code.
