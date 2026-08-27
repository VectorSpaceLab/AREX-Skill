# OpenChat serving deployment

OpenChat's serving entry point is an installed Python module:

```bash
python -m ochat.serving.openai_api_server --model MODEL_REPO_OR_DIR
```

Prefer the bundled wrapper for day-to-day launches because it forwards `--help` but refuses accidental non-help runs without `--model`:

```bash
./scripts/run_openchat_server.sh --help
./scripts/run_openchat_server.sh --model openchat/openchat-3.6-8b-20240522
```

Actual serving requires model weights, a compatible CUDA/PyTorch/vLLM/Ray stack, and enough GPU memory for the model, context length, batch pressure, and tensor-parallel plan.

## Minimum launch decision checklist

1. **Weights**: choose a Hugging Face model id or local model directory for launch `--model`.
2. **Model type**: either ensure `--model` contains `openchat.json` with `model_type`, or pass `--model-type` explicitly.
3. **Client-facing model name**: plan to send a request `model` equal to `/v1/models` output, usually the model type or serving alias.
4. **GPU plan**: decide single GPU vs tensor-parallel multi-GPU; estimate memory before exposing the service.
5. **Exposure/security**: keep default `--host localhost` for local-only use; add API keys and an HTTPS gateway for network exposure.
6. **Logging**: decide whether request/response content can be written to logs. Do not log sensitive prompts in shared deployments.

## Single-GPU launch

```bash
./scripts/run_openchat_server.sh \
  --model openchat/openchat-3.6-8b-20240522 \
  --host localhost \
  --port 18888
```

If the model repository does not include an `openchat.json` file, supply a model type:

```bash
./scripts/run_openchat_server.sh \
  --model SOME_MODEL_REPO_OR_DIR \
  --model-type openchat_3.6 \
  --host localhost \
  --port 18888
```

On GPUs that do not support `bfloat16`, the README recommends adding vLLM's dtype override:

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --model-type openchat_v3.2_mistral \
  --dtype float16
```

## Multi-GPU tensor parallel launch

OpenChat documents tensor parallel serving through vLLM/Ray flags:

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --model-type openchat_v3.2_mistral \
  --engine-use-ray \
  --worker-use-ray \
  --tensor-parallel-size N
```

Use `N` equal to the number of tensor-parallel GPUs assigned to one model replica. The server sets vLLM `max_model_len` to the OpenChat model context length and raises `max_num_batched_tokens` to at least that context length.

Ray/vLLM tips:

- Verify Ray and vLLM import before launch when using multi-GPU flags.
- Ensure CUDA-visible device count is at least `--tensor-parallel-size`.
- If a Ray cluster is already running, confirm it is intended for this serving job before joining or reusing it.
- Do not expect tensor parallelism to fix insufficient per-token KV-cache memory for very high concurrency; reduce request sizes or vLLM batching pressure when necessary.

## Model-type and alias examples

| Launch example | `/v1/models` request names to expect |
|---|---|
| `--model ... --model-type openchat_3.6` | `openchat_3.6` |
| `--model ... --model-type openchat_v3.2_mistral` | `openchat_v3.2_mistral`, `openchat_3.5` |
| `--model ... --model-type openchat_v3.2_gemma_new` | `openchat_v3.2_gemma_new`, `openchat_3.5_gemma_new` |
| `--model ... --model-type chatml_8192` | `chatml_8192` |

Always query `/v1/models` after launch before hard-coding a client request `model`.

## API keys

If `--api-keys` is omitted or empty, endpoints do not require authorization. To require bearer tokens:

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --model-type openchat_3.6 \
  --api-keys "$OPENCHAT_API_KEY_1" "$OPENCHAT_API_KEY_2"
```

Clients must then send:

```bash
-H "Authorization: Bearer ${OPENCHAT_API_KEY_1}"
```

The server checks exact bearer-token values. Do not pass secrets on command lines in shared shell histories if your environment provides a safer process manager secret mechanism.

## System prompts

By default, `system` messages in `messages` are skipped by the async tokenizer. Enable system prompts at launch:

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --model-type openchat_3.6 \
  --enable-sys-prompt
```

This is a launch-time switch; adding a `system` message to a request is not enough.

## Streaming cadence

`--stream-period` controls how often token deltas are emitted for streaming requests. Default: 6 tokens per stream event.

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --stream-period 1
```

Smaller values improve perceived latency but increase event overhead.

## Logging and security

Server-specific log flags:

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --model-type openchat_3.6 \
  --log-file openchat-serving.log \
  --log-max-mb 128 \
  --log-max-count 10
```

When `--log-file` is set, OpenChat writes JSON records containing request payloads and output text. Treat this file as sensitive.

The README's online-service pattern combines API keys, vLLM request-stat suppression flags, and file logging:

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --model-type openchat_3.6 \
  --api-keys "$OPENCHAT_API_KEY" \
  --disable-log-requests \
  --disable-log-stats \
  --log-file openchat-serving.log
```

Security recommendations:

- Keep `--host localhost` unless a network listener is required.
- Put an HTTPS gateway or reverse proxy in front of any internet-facing service.
- Use API keys for non-local clients.
- Restrict CORS instead of accepting every origin in browser-facing deployments.
- Avoid request/output logging for sensitive prompts.

## CORS and network exposure

Defaults in the serving module:

| Flag | Default | Note |
|---|---|---|
| `--host` | `localhost` | Use `0.0.0.0` only when a protected network listener is intended. |
| `--port` | `18888` | Client base URL is `http://HOST:PORT/v1`. |
| `--allowed-origins` | `["*"]` | Parsed as JSON; pass a JSON array string to restrict browser origins. |
| `--allowed-methods` | `["*"]` | Parsed as JSON. |
| `--allowed-headers` | `["*"]` | Parsed as JSON. |
| `--allow-credentials` | false | Enables credentialed CORS requests. |

Restricted browser-facing example:

```bash
./scripts/run_openchat_server.sh \
  --model MODEL_REPO_OR_DIR \
  --model-type openchat_3.6 \
  --host 127.0.0.1 \
  --allowed-origins '["https://chat.example.com"]' \
  --allowed-methods '["POST", "GET"]' \
  --allowed-headers '["Authorization", "Content-Type"]'
```

## Reference-only Docker evidence

The repository includes Docker serving files that show a production-style pattern: install OpenChat, start SSH only when a public key is provided, optionally start a cloudflared tunnel, then launch the API server with `--engine-use-ray --worker-use-ray --disable-log-requests --disable-log-stats` bound to loopback. Use these files as evidence for deployment reasoning only; this generated sub-skill does not bundle or require Docker/SSH/cloudflared helpers.

## Help and vLLM flags

The server parser includes OpenChat-specific flags and all vLLM async engine CLI flags. Inspect the exact installed version's options with:

```bash
./scripts/run_openchat_server.sh --help
```

Because vLLM flag names can change across versions, prefer `--help` from the deployed environment before documenting a production command beyond the stable OpenChat flags above.
