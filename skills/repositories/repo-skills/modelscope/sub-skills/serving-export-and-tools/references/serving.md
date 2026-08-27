# ModelScope serving and vLLM handoff

This reference covers ModelScope's local FastAPI server wrapper and the separate
vLLM runtime pattern that can read ModelScope model identifiers. It is
self-contained and intentionally avoids depending on the original repository
checkout at runtime.

## Choose the right serving surface

| Need | Prefer | Why |
|---|---|---|
| Serve a ModelScope pipeline through simple HTTP endpoints | `modelscope server` | It builds a ModelScope pipeline during FastAPI startup and exposes generic `/describe` and `/call` routes. |
| In-process inference from Python | Route to `../pipelines-and-models/SKILL.md` | The server is a wrapper around pipeline execution, not the shortest path for local batch inference. |
| OpenAI-compatible or high-throughput LLM serving | vLLM runtime with `VLLM_USE_MODELSCOPE=True` | vLLM is a separate server/runtime; ModelScope only provides model-id/cache integration through the environment variable. |
| Download/cache/login policy | Route to `../hub-and-cli/SKILL.md` | The serving command may trigger cache use or download, but hub policy belongs to the hub/CLI skill. |

## ModelScope FastAPI server

The server CLI arguments are implemented by the ModelScope FastAPI wrapper:

- `--model_id` (required): ModelScope model id or a local model directory usable
  by ModelScope model/pipeline loading.
- `--revision` (required): model revision string.
- `--host` (default `0.0.0.0`): bind address. Use `127.0.0.1` for local-only
  development; use `0.0.0.0` only when the network exposure is intentional.
- `--port` (default `8000`): TCP port.
- `--debug` (default string is `debug` in the wrapper): debug/log level value
  passed through the parsed args.
- `--external_engine_for_llm` (default `True`): whether ModelScope's pipeline
  creation should try the external LLM engine path first for LLM models. This is
  not the same as launching a vLLM server; it is an option passed into
  ModelScope pipeline creation. In the inspected wrapper this argument is parsed
  with Python `bool`, so do not assume a CLI string such as `False` disables it;
  verify parsed behavior in the target version before relying on disablement.

Concrete launch template:

```bash
modelscope server \
  --model_id "modelscope/Llama-2-7b-chat-ms" \
  --revision "v1.0.5" \
  --host 127.0.0.1 \
  --port 8000 \
  --debug info \
  --external_engine_for_llm True
```

Operational notes:

1. Startup loads/downloads the model and creates a ModelScope pipeline before
   the app can serve requests. Treat the command as model-loading, not a cheap
   CLI metadata query.
2. The wrapper constructs a FastAPI app and runs it with Uvicorn.
3. The app exposes `/describe`, `/call`, and `/health` routes. `/describe`
   returns task schema and sample input; `/call` accepts JSON shaped according to
   the schema/sample. Binary image/audio/video fields must be base64 encoded.
4. FastAPI interactive docs are available at `http://HOST:PORT/docs` when the
   service is reachable.
5. The server depends on `fastapi`, `sse-starlette`, and `uvicorn`, plus the
   domain/framework extras needed by the selected model.

Health and describe smoke checks after launch:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/describe | python -m json.tool
```

Then send a `/call` request using the sample body from `/describe`, not an
invented payload.

## Docker serving command pattern

The repository README and server documentation describe official CPU/GPU image
families and server-image examples. Treat image tags as examples that may become
stale; pin an image that exists in the target environment.

Generic GPU serving pattern:

```bash
docker run --rm --name modelscope_server \
  --shm-size=50gb \
  --gpus '"device=0"' \
  -e MODELSCOPE_CACHE=/modelscope_cache \
  -v "$HOST_MODELSCOPE_CACHE:/modelscope_cache" \
  -p 8000:8000 \
  "$MODELSCOPE_IMAGE" \
  modelscope server \
    --model_id "modelscope/Llama-2-7b-chat-ms" \
    --revision "v1.0.5" \
    --host 0.0.0.0 \
    --port 8000
```

Safe substitutions:

- For CPU-only experiments, remove `--gpus ...` and choose a CPU image, but do
  not expect large LLMs to fit or run quickly.
- Keep `MODELSCOPE_CACHE` mounted to a persistent host cache if the environment
  permits model downloads. This avoids repeated large downloads.
- Publish only the intended port. If a port is already occupied, choose another
  host port such as `-p 18000:8000` and probe `http://127.0.0.1:18000`.

## vLLM with ModelScope model ids

vLLM support is a separate runtime. The ModelScope server command and a vLLM
server are not interchangeable:

- `modelscope server` uses ModelScope's FastAPI wrapper and generic pipeline
  request/response conversion.
- `python -m vllm.entrypoints...` starts vLLM's own API server. It requires the
  `vllm` package, compatible CUDA/driver/PyTorch stack for GPU serving in most
  practical LLM cases, and a model architecture supported by vLLM.
- `VLLM_USE_MODELSCOPE=True` tells vLLM to resolve ModelScope model ids/cache.
  If the model is not already cached, vLLM may download it from ModelScope.

Non-OpenAI vLLM API server pattern:

```bash
VLLM_USE_MODELSCOPE=True python -m vllm.entrypoints.api_server \
  --model "damo/nlp_gpt2_text-generation_english-base" \
  --revision "v1.0.0" \
  --port 9090
```

OpenAI-compatible vLLM API server pattern:

```bash
VLLM_USE_MODELSCOPE=True python -m vllm.entrypoints.openai.api_server \
  --model "damo/nlp_gpt2_text-generation_english-base" \
  --revision "v1.0.0" \
  --port 9090
```

Docker vLLM pattern:

```bash
docker run --rm --name modelscope_vllm \
  --shm-size=50gb \
  --gpus '"device=0"' \
  -e MODELSCOPE_CACHE=/modelscope_cache \
  -e VLLM_USE_MODELSCOPE=True \
  -v "$HOST_MODELSCOPE_CACHE:/modelscope_cache" \
  -p 9090:9090 \
  "$MODELSCOPE_IMAGE" \
  python -m vllm.entrypoints.openai.api_server \
    --model "modelscope/Llama-2-7b-chat-ms" \
    --revision "v1.0.5" \
    --port 9090
```

Before choosing vLLM, check:

1. Is `python -c "import vllm"` successful in the target environment?
2. Is the model architecture supported by the installed vLLM version?
3. Is the model already cached or is network/cache download allowed?
4. Is there enough GPU VRAM for the model, context length, and concurrency?
5. Does the task require ModelScope's generic `/describe` and `/call` schema? If
   yes, stay with `modelscope server`; vLLM's request schema is different.

## Serving preflight checklist

- Confirm the exact model id or local model directory and revision.
- Confirm whether downloads are allowed. If not, pre-populate the ModelScope
  cache or use a local model directory.
- Confirm server extras and domain/framework extras are installed for the model
  domain.
- Bind to `127.0.0.1` for local development unless remote access is intentional.
- Probe port availability before launch, for example `python - <<'PY'` with a
  socket bind check or `ss -ltnp` if available.
- For GPUs, check driver visibility and memory with `nvidia-smi` where
  available; otherwise treat CUDA serving as unverified.
- Never expose a debug server on a public interface without an upstream auth
  layer, firewall, or other deployment control. The generic wrapper is a local
  development/testing server pattern, not a complete production security stack.
