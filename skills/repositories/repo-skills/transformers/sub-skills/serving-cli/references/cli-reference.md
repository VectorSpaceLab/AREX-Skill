# CLI Reference

This reference summarizes the public Transformers CLI behavior relevant to serving and chat workflows.

## Entrypoint

The distribution exposes the `transformers` console script, which routes to `transformers.cli.transformers:main`.

```bash
transformers --help
transformers version
transformers env
```

If `transformers --help` fails before printing Typer help, first suspect missing base CLI imports such as `requests` or missing package installation metadata. Run:

```bash
python sub-skills/serving-cli/scripts/cli_preflight.py --check-clients
```

## `download`

Use `download` to populate the Hugging Face cache with model and tokenizer files before serving or model discovery.

```bash
transformers download Qwen/Qwen2.5-0.5B-Instruct --cache-dir ./hf-cache
```

Options:

- `MODEL_ID`: Hub model id or compatible source accepted by Auto classes.
- `--cache-dir DIR`: directory where files are saved.
- `--force-download`: redownload even when cache entries exist.
- `--trust-remote-code`: execute custom model code from a model repository; only use after review.

Expected signal: cache contains model blobs, refs, and snapshots. Failure modes: auth/gated model errors, network errors, disk permissions, missing backend package for model class, or unsafe `trust_remote_code` requirements.

## `serve`

The `serve` command starts a FastAPI/Uvicorn server. It is long-lived, so generated agent workflows should construct commands and run preflight by default instead of launching it automatically.

```bash
transformers serve [MODEL_ID] [OPTIONS]
```

### Model loading options

- Positional `MODEL_ID`: preloads and forces one model for all requests; idle auto-unload does not apply to this force-loaded model.
- `--device auto|cpu|cuda:0|mps|...`: inference device selection.
- `--dtype auto|float16|bfloat16|float32|...`: model dtype override; `auto` derives from weights.
- `--trust-remote-code`: allow custom code during model loading.
- `--attn-implementation sdpa|flash_attention_2|...`: select attention backend.
- `--quantization bnb-4bit|bnb-8bit`: request runtime bitsandbytes quantization.
- `--model-timeout SECONDS`: unload idle on-demand models after the timeout; ignored with a force-loaded model.
- `--default-seed N`: set a default torch seed during startup.

### Server options

- `--host localhost`: default safe local binding.
- `--port 8000`: default port.
- `--enable-cors`: add permissive CORS middleware; needed for some browser clients but not recommended for exposed production services.
- `--log-level warning|info|debug|error`: set Transformers logger level.

### Reasoning and chat template options

- `--reasoning auto|on|off`: controls `enable_thinking` only for models/templates that support reasoning.
- `--chat-template-kwargs '{"enable_thinking": true}'`: JSON object forwarded to `apply_chat_template`; request-level `chat_template_kwargs` can override defaults.

### Continuous batching options

- `--continuous-batching`: enable paged-attention continuous batching.
- `--cb-block-size N`: KV cache block size in tokens.
- `--cb-num-blocks N`: number of KV cache blocks.
- `--cb-max-batch-tokens N`: maximum tokens per batch.
- `--cb-max-memory-percent FLOAT`: GPU memory fraction for KV cache, typically between `0.0` and `1.0`.
- `--cb-use-cuda-graph BOOL`: enable CUDA graphs when compatible.

### Compile option

- `--compile`: enable `torch.compile` for faster inference on supported paths. Do not combine it with continuous batching; the serving docs call this incompatible.

## `chat`

`chat` connects to a running server and opens an interactive console.

```bash
transformers chat Qwen/Qwen2.5-0.5B-Instruct http://localhost:8000 max_new_tokens=128 do_sample=False
```

Arguments and options:

- `MODEL_ID`: model id to load/chat with.
- `BASE_URL`: optional positional serving endpoint, defaulting to the local server address.
- Generation flags: trailing `key=value` arguments parsed into a `GenerationConfig` update, such as `temperature=0.7`, `max_new_tokens=256`, `do_sample=False`, or `eos_token_id=[1,2]`.
- Chat prompt commands: `!help`, `!status`, `!clear`, `!example NAME`, `!set key=value`, `!save NAME`, `!exit`.

Expected startup sequence:

1. `chat` checks server health for HTTP(S) base URLs.
2. It posts `{"model": MODEL_ID}` to `/load_model` and renders SSE progress.
3. It sends messages through an async inference client and streams responses.

If step 1 fails, start or locate the server. If step 2 fails, inspect model id, auth, network/cache state, backend memory, and server logs. If step 3 fails, inspect request body fields and generation settings.

## Importability checks

Minimal no-network import checks:

```bash
python - <<'PY'
import importlib
for module in [
    "transformers.cli.transformers",
    "transformers.cli.chat",
    "transformers.cli.download",
    "transformers.cli.serve",
]:
    importlib.import_module(module)
    print("OK", module)
PY
```

Serving import checks can still pass when torch is absent; actual model serving needs backend dependencies and model weights.
