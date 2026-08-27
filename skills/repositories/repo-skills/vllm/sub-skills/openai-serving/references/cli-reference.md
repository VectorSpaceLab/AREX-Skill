# vLLM OpenAI Serving CLI Reference

This reference covers the OpenAI-compatible serving commands owned by this sub-skill. GPU execution, model download, and actual model loading are user-provided environment concerns; verify hardware and memory before running server commands.

## Command map

| Task | Command | Notes |
| --- | --- | --- |
| Start OpenAI-compatible server | `vllm serve MODEL [options]` | Defaults to `http://localhost:8000`; serves one base model identity at a time unless adapters are configured. |
| Interactive chat client | `vllm chat [options]` | Connects to a running OpenAI-compatible server; streams chat completions. |
| Interactive completion client | `vllm complete [options]` | Connects to a running server; streams text completions. |
| Local batch processing | `vllm run-batch -i INPUT.jsonl -o OUTPUT.jsonl --model MODEL` | Processes OpenAI-style JSONL requests locally and writes JSONL responses. |
| Help discovery | `vllm --help`, `vllm serve --help`, `vllm serve --help=Frontend`, `vllm serve --help=all` | Use grouped help to inspect current installed flags. |

## Serve command patterns

Minimal server:

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct
```

Pinned host, port, dtype, context, and memory:

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90
```

Multi-GPU tensor parallel example:

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.92
```

API-key protected server:

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct \
  --api-key sk-local-dev-token
```

Clients must then send `Authorization: Bearer sk-local-dev-token` or use `api_key="sk-local-dev-token"` with the OpenAI client. Multiple keys may be passed to `--api-key` in installations whose help shows `nargs` support.

Browser/front-end CORS example:

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct \
  --host 0.0.0.0 \
  --allowed-origins '["https://app.example.com"]' \
  --allowed-methods '["GET", "POST", "OPTIONS"]' \
  --allowed-headers '["Authorization", "Content-Type"]' \
  --allow-credentials
```

The CORS list flags are JSON values, not comma-separated strings. Keep `--allow-credentials` off unless the browser app needs credentialed requests.

Useful lifecycle/logging flags from the OpenAI frontend include:

- `--uvicorn-log-level debug` for request routing and server startup detail.
- `--disable-uvicorn-access-log` or `--disable-access-log-for-endpoints /health,/metrics` to reduce health-check log noise.
- `--enable-request-id-headers` to add `X-Request-Id` headers.
- `--log-error-stack` for server-side stack traces during development.
- `--root-path /prefix` when a reverse proxy mounts the API under a path.
- `--ssl-keyfile`, `--ssl-certfile`, and related SSL flags when terminating TLS in vLLM rather than a proxy.

## Readiness and model discovery

Validate the process before sending generation traffic:

```bash
curl -f http://localhost:8000/health
curl http://localhost:8000/v1/models
```

Expected `/v1/models` response shape is an OpenAI-style model list with `data[].id`. Use one of those IDs as the client `model` argument. Do not assume the Hugging Face repo name if `--served-model-name`, LoRA, or other model aliasing is configured; discover the served name.

## `vllm chat`

`vllm chat` is a thin OpenAI client for a running server:

```bash
vllm chat --url http://localhost:8000/v1 --model-name Qwen/Qwen2.5-1.5B-Instruct
```

One-shot mode:

```bash
vllm chat \
  --url http://localhost:8000/v1 \
  --model-name Qwen/Qwen2.5-1.5B-Instruct \
  --api-key sk-local-dev-token \
  --system-prompt "You are concise." \
  --quick "Write one sentence about vLLM."
```

If `--model-name` is omitted, the command lists models and uses the first returned ID. `--api-key` overrides `OPENAI_API_KEY`; otherwise it falls back to `OPENAI_API_KEY` and then a dummy token.

## `vllm complete`

`vllm complete` targets `/v1/completions` and streams text completion chunks:

```bash
vllm complete \
  --url http://localhost:8000/v1 \
  --model-name Qwen/Qwen2.5-1.5B-Instruct \
  --max-tokens 64 \
  --quick "A robot may not injure"
```

Use `complete` for legacy prompt-completion style models or compatibility tests. Use `chat` for instruction/chat models with message lists.

## `vllm run-batch`

`run-batch` reads OpenAI Batch-style JSONL and writes JSONL responses:

```bash
vllm run-batch \
  -i requests.jsonl \
  -o responses.jsonl \
  --model Qwen/Qwen2.5-1.5B-Instruct
```

Each input line is a JSON object with:

```json
{"custom_id":"req-1","method":"POST","url":"/v1/chat/completions","body":{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Say hello"}],"max_tokens":32}}
```

Supported batch URL families include `/v1/chat/completions`, `/v1/embeddings`, `/score`, `/rerank`, `/v1/audio/transcriptions`, and `/v1/audio/translations`, but the exact supported task depends on the served model. Chat batch limitations include no streaming, no tool use, no beam search, and `n=1`.

`run-batch` also has local metrics options; when enabled it exposes Prometheus metrics at `/metrics` on the configured host/port. For embeddings, rerank, score, audio, LoRA, and multimodal specifics, route to `../modalities-adapters-pooling/SKILL.md`.

## Validation checklist

Before handing off a serving workflow:

1. Confirm `vllm serve --help` in the user's installed environment for version-specific flags.
2. Build the command with model, host/port, auth, and only the engine flags needed for the user's hardware.
3. Mark model download/GPU loading as hardware-gated and user-provided.
4. Verify `/health` and `/v1/models` before generation.
5. Use the discovered `data[].id` as the OpenAI client `model`.
6. Keep `base_url` ending in `/v1` for OpenAI Python clients.
