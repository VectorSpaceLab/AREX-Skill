---
name: inference-and-serving
description: "Use this sub-skill for LlamaFactory inference, ChatModel usage,
  chat/webchat/api commands, OpenAI-compatible serving, backend selection,
  streaming, score evaluation, API auth, and batch vLLM prediction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Serving

Use this sub-skill when an agent needs to run or debug LlamaFactory inference and serving flows for version `0.9.6.dev0` source behavior.

## Route Here For

- Using `ChatModel` from Python for `chat`, `stream_chat`, `get_scores`, and their async variants.
- Launching `llamafactory-cli chat`, `lmf chat`, `llamafactory-cli webchat`, `llamafactory-cli api`, or `lmf api`.
- Calling the OpenAI-compatible FastAPI server endpoints `/v1/models`, `/v1/chat/completions`, and `/v1/score/evaluation`.
- Choosing `infer_backend: huggingface`, `infer_backend: vllm`, or `infer_backend: sglang` for inference configs.
- Diagnosing streaming SSE, API key, score-vs-chat endpoint, and missing backend package failures.
- Planning safe batch prediction with vLLM and optional BLEU/ROUGE-style metric output.

## Boundaries

- Route model, tokenizer, quantization, adapter merge, and export failures to the `model-loading-and-export` sub-skill.
- Route template, prompt formatting, multimodal placeholder, dataset, and preprocessing issues to `data-and-templates` unless the failure is specific to API request payload handling.
- Route non-API LlamaBoard/Web UI install, browser, port, and operational issues to `webui-and-ops`.
- Keep runtime instructions self-contained; do not depend on repository checkout scripts or examples.

## Fast Path

1. Pick an inference config YAML with `model_name_or_path`, `template`, and `infer_backend`; the default architecture is v0 unless `USE_V1=1` is explicitly set.
2. For local interactive testing, run `llamafactory-cli chat CONFIG.yaml` or `lmf chat CONFIG.yaml`.
3. For OpenAI-compatible serving, run `API_PORT=8000 llamafactory-cli api CONFIG.yaml` and call `http://HOST:PORT/v1/...` endpoints.
4. Use `API_KEY` only when bearer-token auth is desired; clients must send `Authorization: Bearer $API_KEY` when it is set.
5. Prefer `infer_backend: huggingface` for broad compatibility and score evaluation; use `vllm` or `sglang` for faster generation when those optional packages and GPU resources are available.

## Bundled References

- `references/chat-and-api.md` covers `ChatModel`, CLI commands, API routes, request shapes, streaming, auth, env vars, and native verification candidates.
- `references/backend-selection.md` compares Hugging Face, vLLM, and SGLang inference backends and includes batch vLLM metric flow notes.
- `references/troubleshooting.md` maps common serving failures to likely causes and fixes.

## Bundled Scripts

- `scripts/openai_api_smoke.py` is a standalone OpenAI-compatible smoke client for model listing, chat, optional streaming, optional score evaluation, and API-key verification.
- `scripts/vllm_batch_infer.py` is a safe wrapper that prints or optionally runs a LlamaFactory batch vLLM command only when the caller supplies concrete model/config arguments.
