---
name: api-serving
description: "Routes Chinese-LLaMA-Alpaca-2 FastAPI and OpenAI-compatible
  serving workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# api-serving

Use this sub-skill when the task is to expose Chinese-LLaMA-Alpaca-2 through an HTTP service, especially an OpenAI-compatible completion or chat endpoint.

## Use it when

- the user mentions `openai_api_server.py`, `openai_api_protocol.py`, FastAPI, Uvicorn, or SSE streaming
- the task is about `/v1/completions`, `/v1/chat/completions`, `/v1/models`, request validation, or response schemas
- the user asks how to serve a base model plus optional LoRA adapter
- the task is about optional vLLM serving constraints

## Workflow

1. Read `references/workflows.md` for endpoint, server, and request-schema details.
2. Use `scripts/openai_server_demo/openai_api_server.py` for the non-vLLM FastAPI server.
3. Use the vLLM script only after installing the optional vLLM/FastChat stack.
4. Confirm model path, tokenizer path, LoRA path, quantization, and CPU/GPU flags before launch.
5. Read `references/troubleshooting.md` for model-name, optional dependency, and serving-runtime failures.

## Bundled runtime files

- `scripts/openai_server_demo/openai_api_server.py`
- `scripts/openai_server_demo/openai_api_protocol.py`
- `scripts/openai_server_demo/openai_api_server_vllm.py` (optional dependency path)
- `scripts/openai_server_demo/openai_api_protocol_vllm.py` (optional dependency path)
- `scripts/attn_and_long_ctx_patches.py`

## What to read first

- `references/workflows.md` for endpoint shape and server flags
- `references/troubleshooting.md` for optional vLLM, LoRA, quantization, and model-name issues

## Routing notes

- Use this sub-skill for HTTP service behavior and request/response schemas.
- Use `hf-inference` for direct local generation with no server.
- Use `local-integrations` for llama.cpp server wrappers rather than the FastAPI server.
