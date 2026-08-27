---
name: qwen
description: "Use QwenLM/Qwen for Qwen model loading, local generation, serving,
  fine-tuning, quantization, evaluation, system prompts, tool use, and
  tokenizer-aware workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qwen

Use this skill when a task names Qwen, Qwen-7B/Qwen-14B/Qwen-72B, Qwen-Chat, `Qwen/Qwen-*`, ModelScope Qwen checkpoints, Qwen's Transformers examples, `qwenllm/qwen` Docker images, or the repository's fine-tuning, evaluation, serving, tokenizer, and tool-use workflows.

This is a repository operating graph, not a general model card. Start by deciding whether the request is about a base model or a chat model, whether the checkpoint is remote or local, and whether the desired action needs CPU, CUDA, Docker, a vendor accelerator, a cloud API, credentials, or a sandbox.

## Fast start

- Base install for the documented Transformers workflows: `pip install -r requirements.txt`.
- Add only the optional dependency family needed by the route: web demo, API server, PEFT/DeepSpeed, AutoGPTQ, vLLM/FastChat, ModelScope, or a vendor runtime.
- Safe environment check: `python scripts/check_qwen_environment.py --check-dependencies`.
- Minimal public-package check: `python -c "import torch, transformers, tiktoken; print(torch.__version__, transformers.__version__)"`.
- Do not download a checkpoint, start a service, run training, run a benchmark, or use a cloud key merely to prove that the package imports.

## Route by task

| User request | Read first |
| --- | --- |
| Load Qwen with Transformers/ModelScope, chat, batch generation, CPU/multi-GPU, precision, local checkpoints, long context, or quantized inference | `sub-skills/inference-model-loading/SKILL.md` |
| Run the CLI/Web UI/OpenAI-compatible API, vLLM/FastChat, Docker, TensorRT, Ascend, or DCU deployment | `sub-skills/serving-deployment/SKILL.md` |
| Prepare SFT data, full fine-tuning, LoRA, Q-LoRA, DeepSpeed/FSDP, adapter merge, or GPTQ quantization | `sub-skills/finetuning-quantization/SKILL.md` |
| Reproduce C-Eval, MMLU, CMMLU, GSM8K, HumanEval, or plugin/tool-use benchmarks | `sub-skills/evaluation-reproduction/SKILL.md` |
| Use system prompts, ReAct, function calling, Hugging Face Agent patterns, ChatML, special tokens, or BPE merge extension | `sub-skills/prompting-tool-use-tokenization/SKILL.md` |

## Cross-cutting rules

1. Prefer a local checkpoint path when the user already has one. A model identifier such as `Qwen/Qwen-7B-Chat` or `qwen/Qwen-7B-Chat` implies a download and remote-code execution; state that prerequisite explicitly.
2. Keep `trust_remote_code=True` explicit for these historical Qwen checkpoints. Verify the checkpoint contains its config, tokenizer files, model shards, and any required `qwen.tiktoken` file before diagnosing Python code.
3. Never treat a CPU import or a tiny CUDA tensor as proof that full model generation, training, vLLM, GPTQ, or benchmark performance works. Report hardware, memory, model size, and optional dependency gates separately.
4. Treat `Qwen-*` base models and `Qwen-*-Chat` models differently: base models are for continuation; chat models provide `chat`/`chat_stream` and alignment behavior.
5. Use the bundled helpers for dry-run command construction and local validation. They do not load models, download data, launch services, invoke Docker, or execute generated code.

## Shared references

- Read `references/model-family-overview.md` for model names, context, precision, quantization, and backend planning.
- Read `references/troubleshooting.md` for install/import, checkpoint, tokenizer, optional dependency, hardware, license, and safety failures.
- Read `references/repo-provenance.md` before deciding whether this graph is stale for a newer checkout.
- Read `references/repo-routing-metadata.json` only when maintaining managed router placement; it is structured metadata, not a prose route.

## Scope and safety

The repository contains historical GPU-heavy and vendor-specific workflows. Keep network, credentials, Docker, public sharing, generated-code execution, model downloads, training, and long-running servers explicit and user-approved. Preserve Qwen's license and safety obligations and perform application-specific red-teaming before deployment.
