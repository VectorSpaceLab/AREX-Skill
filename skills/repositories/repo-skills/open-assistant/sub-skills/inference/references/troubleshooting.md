# Inference troubleshooting

## Unknown model config

**Symptoms**

- Worker logs `Unknown model config name: ...` and exits with status 2.
- `check_inference_config.py --model-config <name>` exits nonzero.

**Likely causes**

- Typo or wrong case in `MODEL_CONFIG_NAME`.
- Config existed in a different revision of the shared model registry.

**Recovery**

1. Run `python scripts/check_inference_config.py --repo-root <repo-root> --list`.
2. Choose `_lorem` for protocol checks or a listed model name for real generation.
3. Restart the worker after changing `MODEL_CONFIG_NAME`.

## Wrong API key or protocol upgrade

**Symptoms**

- Worker receives `wrong_api_key` from websocket.
- Worker receives `upgrade_protocol` and exits with status 2.
- Websocket bad status exceptions occur immediately after connecting.

**Recovery**

- Match worker `API_KEY` to the server's configured debug or database worker key.
- Confirm worker header `X-Protocol-Version` matches shared `INFERENCE_PROTOCOL_VERSION` used by the server.
- Do not paper over `upgrade_protocol`; use compatible server/worker/shared sources.

## Redis/Postgres/Alembic startup failures

**Symptoms**

- Server logs repeated Alembic upgrade retries.
- Rate limiter setup fails to connect to Redis.
- `/configs/model_configs` or `/chats` never becomes healthy.

**Recovery**

1. Confirm `inference-db` and `inference-redis` containers are healthy.
2. Check `POSTGRES_HOST`, `POSTGRES_DB`, `REDIS_HOST`, and ports.
3. For local dev, use the compose inference profile service names inside containers and host ports only from the host.
4. If Alembic is intentionally skipped, ensure schema already matches server models.

## Text-generation backend not connected

**Symptoms**

- Worker waits for inference server or TGI connection.
- Real model worker never accepts work.

**Likely causes**

- `INFERENCE_SERVER_URL` points to the wrong port or service.
- TGI container is not started or still downloading/loading weights.
- LLaMA model requires an image/runtime variant that supports LLaMA.

**Recovery**

- Use `_lorem` first to isolate server/worker websocket health.
- For real models, wait for text-generation server connected/ready logs.
- Verify model id and image tag before diagnosing chat routes.

## Model download, cache, or Hugging Face auth failures

**Symptoms**

- Transformers or Hugging Face hub errors while loading tokenizer/model.
- Permission errors in cache directories.
- Private/gated model access errors.

**Recovery**

- Ask the user before triggering downloads.
- Set a writable cache directory and be careful when containers run as root.
- Provide valid HF tokens only through environment or runtime secrets, not in generated docs or committed files.
- Use `distilgpt2` or `_lorem` to separate cache/auth issues from inference protocol issues.

## GPU out of memory

**Symptoms**

- CUDA OOM during model load or first generation.
- Worker can load tokenizer but fails after first work request.
- More failures after increasing `MAX_PARALLEL_REQUESTS`.

**Recovery**

1. Estimate memory: non-quantized params(B) × 2.5 GB; quantized q configs × 1.25 GB.
2. Leave headroom for KV cache and concurrency.
3. Lower `MAX_PARALLEL_REQUESTS`, use a quantized config, choose a smaller model, or use `_lorem` for non-model checks.
4. Do not call a CPU-only check proof of GPU readiness.

## SSE client errors

**Symptoms**

- Text client raises JSON decode errors for event data.
- Browser receives no final message after tokens.
- Pending events never resolve.

**Recovery**

- Confirm server sends SSE with `Accept: text/event-stream`.
- Treat `ping` as keepalive and `pending` as wait state.
- `token` events append text; `message` marks complete; `error` must be surfaced.
- For browser chunk line buffering, route to the `website` sub-skill.

## Plugin OpenAPI failures

**Symptoms**

- Plugin config cannot be downloaded/parsed.
- Unsupported content type or missing `$ref` component errors.
- Tool execution does not produce final prompt.

**Recovery**

- Verify plugin config URL and its `api.url`.
- Accept only JSON/YAML OpenAPI specs.
- Treat plugin preparation errors as optional plugin failures unless the user's task specifically depends on that plugin.
- Disable plugins to isolate base model/chat behavior.

## Safety server not available

**Symptoms**

- Worker safety request fails.
- Safety label parsing returns unexpected output.

**Recovery**

- Disable safety for base inference smoke checks.
- Start the safety server only when safety behavior is the task target.
- Check safety level range [0, 9] and Blade2Blade service availability.
