---
name: openai-llm-frontend
description: "Launch and use Triton's OpenAI-compatible LLM frontend over vLLM
  or TensorRT-LLM backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenAI LLM Frontend

Use this sub-skill when the task involves Triton's OpenAI-compatible FastAPI frontend, `/v1/chat/completions`, `/v1/completions`, embeddings, model-list/load/unload APIs, vLLM/TensorRT-LLM backend serving, LoRA selection, tool calling, request-size limits, or restricted OpenAI API groups.

## Route Within This Sub-skill

- **Launch command, CLI flags, backend/tokenizer/model-control choices, optional KServe frontends**: read [`references/cli-reference.md`](references/cli-reference.md) and use [`scripts/build_openai_frontend_command.py`](scripts/build_openai_frontend_command.py).
- **OpenAI-compatible request schemas, streaming, LoRA, tool calling, model endpoints, Python client usage**: read [`references/openai-api-reference.md`](references/openai-api-reference.md) and use [`scripts/build_openai_request.py`](scripts/build_openai_request.py).
- **Backend/tokenizer/HF token/runtime failures, `--load-model` rules, restricted API 401, request-size 413, malformed tool calls**: read [`references/troubleshooting.md`](references/troubleshooting.md).

If the user asks for KServe `/v2/*` payloads, route to [`../client-protocols/SKILL.md`](../client-protocols/SKILL.md). If the user asks for generic runtime containers and metrics, route to [`../server-runtime-and-deployment/SKILL.md`](../server-runtime-and-deployment/SKILL.md).

## Safe Default Workflow

1. Confirm model repository, backend (`vllm` or `tensorrtllm`), tokenizer path/Hugging Face ID, GPU/runtime availability, and whether model downloads are approved.
2. Build a dry-run command with the CLI helper. Do not start the frontend without runtime approval.
3. Build request JSON with the request helper before sending live `/v1/*` calls.
4. Distinguish OpenAI frontend port `9000` from KServe HTTP port `8000` and gRPC port `8001`.
5. Verify live startup only when the correct container variant, model repo, tokenizer, and GPU backend are available.
