# Troubleshooting Serving CLI

## `transformers --help` fails before printing help

Likely causes:

- Base install is incomplete.
- `requests` is missing, which can break import of the chat command while the top-level CLI app is assembled.
- Typer or `huggingface_hub` CLI helpers are missing or mismatched.

Checks:

```bash
python sub-skills/serving-cli/scripts/cli_preflight.py --check-clients
python -c "import requests, typer, huggingface_hub; print('ok')"
```

Fix: install the missing package reported by preflight. For serving workflows, prefer `pip install "transformers[serving]"` when available; otherwise install the named missing dependency explicitly.

## `transformers serve` raises missing serving dependencies

Signal: `ImportError` mentions installing `transformers[serving]`, or missing `fastapi`, `uvicorn`, `pydantic`, or `openai`.

Checks:

```bash
python sub-skills/serving-cli/scripts/cli_preflight.py --check-serving
```

Fix: install serving extras and rerun preflight. Remember that serving extras are separate from model backend packages such as `torch`.

## PyTorch-dependent classes fail

Signal: optional dependency `ImportError` when importing/loading model classes, or serve starts but model requests fail during loading.

Cause: minimal Transformers import can succeed without torch; model-backed serving cannot. Install an appropriate torch build for the machine and rerun a tiny model load or preflight that reports torch presence.

## Port conflict

Signal: Uvicorn reports address already in use, or preflight says the port is not available.

Checks:

```bash
python sub-skills/serving-cli/scripts/cli_preflight.py --host localhost --port 8000
```

Fix: choose a free port with `--port`, stop the existing service, or point clients at the already-running service if it is the intended one.

## CORS/browser client cannot connect

Signal: browser console shows CORS errors while CLI/curl works.

Fix: start the server with `--enable-cors` only for trusted local browser integrations:

```bash
transformers serve --host localhost --port 8000 --enable-cors
```

Do not expose a permissive CORS server on an untrusted network without a proxy and access controls.

## Chat server unavailable

Signal: `transformers chat` cannot connect, health check fails, or `/load_model` request errors.

Checks:

```bash
curl http://localhost:8000/health
python sub-skills/serving-cli/scripts/cli_preflight.py --base-url http://localhost:8000 --probe-health
```

Fix: start the server, correct the positional `BASE_URL`, resolve port conflicts, or inspect server logs for dependency/model-load failures.

## `/load_model` SSE fails

Signals:

- HTTP validation error when `model` is missing.
- Error event for nonexistent or gated model.
- Download/auth/network failures.
- OOM or backend import errors during weights loading.
- Client appears hung because it buffers SSE.

Checks:

```bash
curl -N -X POST http://localhost:8000/load_model \
  -H "Content-Type: application/json" \
  -d '{"model":"MODEL_ID"}'
```

Fixes: use `curl -N` or a streaming-capable client, authenticate for gated models, use local cached paths when offline, lower dtype/memory pressure, or install missing backend packages.

## Model timeout/unload surprises

Signal: first request after idle period is slow because the model was unloaded and reloaded.

Fix: increase `--model-timeout`, force-load a model by passing positional `MODEL_ID`, or explicitly warm with `/load_model` before latency-sensitive checks. `--model-timeout` is ignored for a force-loaded model.

## `trust_remote_code` requirement

Signal: model load asks for or requires custom repository code.

Fix: do not set `--trust-remote-code` automatically. Review the model repository code and only then pass:

```bash
transformers serve MODEL_ID --trust-remote-code
transformers download MODEL_ID --trust-remote-code
```

If review is not possible, choose a model with native Transformers support.

## Continuous batching incompatibilities

Signals:

- Startup or request errors after `--continuous-batching`.
- 503 errors caused by continuous batching worker death.
- Shape/cache/backend errors under concurrent requests.
- Performance worsens due to unsuitable KV cache sizing.

Fixes:

1. Retry without `--continuous-batching` to isolate the issue.
2. Remove `--compile`; compile is documented as incompatible with continuous batching.
3. Use a supported attention backend such as `sdpa` before trying specialized kernels.
4. Reduce `--cb-max-batch-tokens`, `--cb-num-blocks`, or `--cb-max-memory-percent`.
5. Confirm torch, GPU, dtype, and model architecture compatibility.

## Quantization or attention backend fails

Signal: missing `bitsandbytes`, flash attention import errors, dtype/device mismatch, or unsupported hardware.

Fix: remove the optimization flag first to prove baseline serving, then route quantization decisions to [../quantization-integrations/SKILL.md](../../quantization-integrations/SKILL.md). For attention backend errors, use `--attn-implementation sdpa` as a conservative fallback.

## Reasoning flag has no visible effect

Cause: `--reasoning on|off|auto` only changes chat template kwargs for models/templates that support `enable_thinking` or declare thinking delimiters.

Fix: verify the selected model supports reasoning. Check response fields for `reasoning_content`; do not expect hidden reasoning to appear in normal `content`.

## Streaming client appears stuck

Causes:

- Client buffers SSE.
- Server is still downloading/loading model.
- Request triggered long generation due to missing token limit.
- Backend is OOM or worker died.

Fixes: use `curl -N`, set `max_tokens` or `max_output_tokens`, warm the model first with `/load_model`, inspect server logs, and start with non-streaming requests.
