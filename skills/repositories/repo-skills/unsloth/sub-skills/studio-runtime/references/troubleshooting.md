# Studio Troubleshooting

Start with non-destructive checks. Do not run installers, updates, uninstallers, or model downloads unless the user asks or approves.

## First Five Checks

1. Run the safe bundled preflight: `python scripts/studio_preflight.py --host 127.0.0.1 --port 8888`.
2. Confirm CLI availability: `unsloth --help`, `unsloth studio --help`, `unsloth studio run --help`.
3. Confirm intended Studio root: `UNSLOTH_STUDIO_HOME`, `STUDIO_HOME`, or default `~/.unsloth/studio`.
4. Check health if server should already be running: `GET http://127.0.0.1:<port>/api/health`.
5. If a model should be loaded, check `/api/inference/status` and `/v1/models` with the correct bearer key.

## Common Symptoms and Fixes

| Symptom | Likely Causes | Checks | Fix |
| --- | --- | --- | --- |
| `Studio not set up. Run install.sh first.` | Studio venv missing; `UNSLOTH_STUDIO_HOME` points to an empty/wrong root; launcher from a different install | Preflight root summary; `unsloth studio --help`; confirm `UNSLOTH_STUDIO_HOME` is same as setup | Use the same root at setup and launch; rerun public installer or `unsloth studio setup` if user approves. |
| Missing frontend / 404 UI | Packaged frontend `dist` absent; wrong launcher points to a package without built frontend; invalid `--frontend` | Error mentions frontend build not found; check `--api-only` need | Rerun setup/update; pass a valid built `frontend/dist`; use `--api-only` only when no UI is needed. |
| Browser cannot open `localhost` | Studio binds IPv4 `127.0.0.1`; local resolver returns IPv6-only `::1`; different process on `::1` | Try `http://127.0.0.1:<port>` | Open IPv4 loopback URL or bind/route intentionally. |
| Port already in use | Another process or another Studio owns requested port | Startup reports alternate port; preflight socket check | Use reported port, stop blocker, or choose `-p <free_port>`. |
| `UNSLOTH_CPU_THREADS` error | Value is non-integer, zero, or negative | Preflight env warnings | Set a positive integer or unset it. |
| Server starts but agent cannot auth | Wrong API key; remote server without saved key; local identity proof mismatch; key expired/revoked | `GET /v1/models` with bearer key; `UNSLOTH_STUDIO_URL`; key cache per exact base | Create/revoke/recreate API key; pass `--api-key` or `UNSLOTH_API_KEY`; verify URL and port. |
| `unsloth connect codex` rejects model | Active model is transformer backend; Codex needs GGUF for streamed `/v1/responses` | `/api/inference/status` `is_gguf` | Load a GGUF model, e.g. `unsloth connect codex --model <model>-GGUF`. |
| Tools not available | `--disable-tools`; request/UI disabled tools; stdio MCP gate off; external host default policy | Launch flags; request payload; `UNSLOTH_STUDIO_ALLOW_STDIO_MCP` | Remove/adjust disabling flag, enable per-chat tools, or explicitly opt into stdio MCP only when safe. |
| Tools too exposed | Raw bind or shared tunnel with tools enabled | Launch command and server banner | Relaunch with `--disable-tools`, rotate API key if shared. |
| Cloudflare link absent | `--no-cloudflare`; `--api-only`; Colab/proxy environment; download/cache failure; blocked quick-tunnel connection | Startup logs; secure flag; network restrictions | For remote safe access use `--secure`; if secure fails closed, fix tunnel/network or choose a deliberate raw bind. |
| Secure launch exits instead of raw fallback | `--secure` could not start a registered Cloudflare tunnel | Startup error | This is expected fail-closed behavior. Fix tunnel availability or use `--no-secure -H 0.0.0.0` only with explicit risk acceptance. |
| `--secure` with `--no-cloudflare` rejected | Contradictory flags | Command line | Remove `--no-cloudflare` or use raw bind without `--secure`. |
| API provider test fails | Bad key, wrong base URL, custom provider missing model ID, fingerprint changed, model filters exclude results | `/api/providers/public-key`, `/api/providers/test`, `/api/providers/models` | Refresh page/client, re-enter encrypted key, correct base URL/model ID/provider type. |
| RAG endpoints return `503` | `sqlite-vec` extension unavailable | `/api/rag/knowledge-bases` response detail | Install/fix RAG dependencies through setup; do not retry ingestion until extension loads. |
| RAG upload rejected | Unsupported extension, empty file, too large, extraction failure | Response status/detail; RAG/data recipe job events | Use supported files, reduce size, inspect extraction logs/events. |
| RAG preview fails | Expired signed URL, missing stored file, token mismatch, file outside upload root | Refresh file-url route; check document still exists | Mint a new preview URL; re-ingest if stored file missing. |
| Shutdown hangs or leaves model process | llama-server/export/training/cloudflared subprocess cleanup in progress or stuck | Server logs; process list after graceful shutdown | Use UI shutdown or Ctrl+C once; wait. If orphan remains, terminate only the child process after confirming it belongs to Studio. |

## `UNSLOTH_STUDIO_HOME` Problems

`UNSLOTH_STUDIO_HOME` is the most common root-cause for confusing setup/runtime mismatches.

Expected behavior:

- `UNSLOTH_STUDIO_HOME` wins over `STUDIO_HOME`.
- A custom root is used for Studio-managed venv, auth, database, cache, outputs, exports, RAG, and custom-root llama.cpp.
- The runtime re-exports `UNSLOTH_LLAMA_CPP_PATH` for custom roots if unset.
- Launchers use same-install discriminators so one Studio install should not accidentally attach to another root's backend.

Troubleshooting:

- If setup was run with a custom root, launch with the same env var.
- If a default install is accidentally launched with a leaked `UNSLOTH_STUDIO_HOME`, unset it and retry.
- If a custom root is not writable, setup should fail clearly; choose a writable directory.
- If root resolution crashes due to restricted filesystem paths, prefer explicit `UNSLOTH_STUDIO_HOME` to a normal writable path.
- Do not hard-code private absolute roots in public instructions; use placeholders.

## Setup/Update/Uninstall Failures

Setup scripts and install helpers can mutate the machine, install dependencies, build assets, download prebuilt tools, or remove files. Ask before running them.

Common setup issues:

- Python stack install failed: rerun setup after fixing Python/package manager prerequisites.
- Node/prebuilt frontend setup failed: rerun setup/update; if only API is needed, use `--api-only` temporarily.
- llama.cpp prebuilt install/update failed: inspect `/api/llama/update-status`; source builds may not support the same update path.
- Custom root ownership guard rejects destructive mutation: the target path may not be Studio-owned. Choose a clean root or confirm cleanup with the user.
- Workspace guard rejects install in unsafe location: run from a normal user workspace rather than system directories.

Uninstall guidance:

- Public uninstall scripts remove Studio install data, launcher integration, shortcuts, and platform-specific entries.
- Manual deletion of the install directory can leave launchers/shortcuts behind.
- Hugging Face model cache is not removed by the documented uninstall scripts.

## Remote Access and Coding-Agent Cases

### Case: Remote Studio launch with HTTPS tunnel and agent connection

Symptoms:

- User wants to access Studio from another machine or connect Codex/Claude.
- Raw `localhost` URL works only on the host machine.
- User may be tempted to use `-H 0.0.0.0`.

Plan:

1. Prefer `unsloth studio --secure -p 8888 --disable-tools` for browser/API access.
2. Confirm the Cloudflare URL printed by the server.
3. Create or pass an API key. Remote clients need explicit key handling; local auto-minting is only for verified loopback.
4. Set `UNSLOTH_STUDIO_URL` to the HTTPS tunnel URL for the client if needed.
5. Use `unsloth connect <agent> --api-key <key>` or print env with `--no-launch` when launching on another shell.
6. If tools are required, replace `--disable-tools` with an explicit `--enable-tools` only in a trusted/disposable environment and rotate the key afterwards.

If `--secure` fails, do not silently switch to raw bind. Explain fail-closed behavior and ask whether the user wants to fix the tunnel/network or accept raw `-H 0.0.0.0` risk.

## llama.cpp, GGUF, mmproj, Cache, and Context

### Load/Generation Failure Checklist

1. Validate the model: `/api/inference/validate` with `model_path`, optional `gguf_variant`, and intended context/cache settings.
2. List variants: `/api/models/gguf-variants?repo_id=...` or UI equivalent. Confirm the variant exists and is downloaded if local-only mode is expected.
3. Check `/api/inference/load-progress` during heavy loads; mmap/GPU upload can appear stalled for large models.
4. Check `/api/inference/status` after load for `is_gguf`, `gguf_variant`, `context_length`, `cache_type_kv`, `tensor_parallel`, and capability flags.
5. Check context errors: context overflow maps to a structured `context_length_exceeded` style error in several routes.
6. If first token times out, reduce context, increase GPU offload, lower parallel slots, load a smaller/quantized model, or disable expensive extras.
7. If generation stops mid-response, treat it as model-server crash/disconnect until proven otherwise.

### mmproj / Vision GGUF Problems

Symptoms:

- Vision/chat-with-images fails for a GGUF model.
- Load works but image input is ignored or errors.
- User passed llama extras that change mmproj behavior.

Checks:

- Confirm `has_vision` from GGUF variants or model metadata.
- Confirm companion `mmproj` exists for the selected GGUF/repo.
- Check whether extras include last-wins `--no-mmproj` or `--no-mmproj-auto`.
- For native/local leased files, companion files must live next to the selected GGUF.
- Avoid passing Studio-managed `--mmproj`/`--mmproj-url` through raw extras; Studio rejects those.

Fixes:

- Select a vision-capable GGUF repo/variant with the proper companion.
- Remove `--no-mmproj` unless intentionally disabling vision.
- Refresh/download the correct companion through Studio-managed model flows.

### Context and KV Cache Problems

Symptoms:

- Context overflow errors.
- OOM during load or first prompt.
- Very slow or failed multi-request serving.

Checks:

- `--parallel N` divides usable KV cache across slots; `studio run` defaults to 4 and plain Studio defaults to 1.
- `-c` / `--ctx-size` pass-through can override context for GGUF.
- `cache_type_kv` or `--cache-type-k`/`--cache-type-v` changes memory use.
- `/api/models/kv-cache-estimate` can estimate memory pressure before load.
- Large RAG/chat histories plus tools can exceed context even if the model loaded.

Fixes:

- Lower `--parallel` for long-context single-user work.
- Lower context or use more compact cache types.
- Reduce RAG/document/message history or use truncation/compaction.
- Use a smaller/more quantized model or stop concurrent training before loading chat.

### llama.cpp Freshness and Update Problems

Startup probes check llama.cpp capability/freshness off the critical path. `/api/llama/update-status` reports whether a prebuilt install is supported, stale, and updateable.

Fixes:

- If MTP/speculative features are missing, check update status.
- If the install is source-built, prebuilt update may report unsupported/source-build behavior.
- `POST /api/llama/update` downloads and atomically swaps the prebuilt; ask before running.

## Hardware Detection

### NVIDIA/CUDA

- Studio pins `CUDA_DEVICE_ORDER=PCI_BUS_ID` early so GPU indices match `nvidia-smi` PCI-bus ordering.
- `CUDA_VISIBLE_DEVICES` can remap GPUs; explicit `gpu_ids` are physical indices and unsupported when parent visibility uses UUID/MIG entries.
- GPU memory guards can refuse loading a chat model while training if insufficient free VRAM remains.

### Apple/MLX

- macOS can use MLX and GGUF inference paths.
- For Apple hosts, failures often involve missing native dependencies, wrong architecture, or stale llama.cpp prebuilt.
- Use `/api/system/hardware` and model modality/status endpoints to distinguish MLX vs GGUF vs transformer backend.

### Windows ROCm / AMD

- Windows ROCm DLL directories are registered before torch import when HIP/ROCm paths exist.
- `hipInfo.exe` can be added to PATH from the venv scripts directory when available.
- `BNB_ROCM_VERSION` may be detected from installed bitsandbytes ROCm DLLs.
- On WSL AMD Strix Halo, `HSA_ENABLE_DXG_DETECTION=1` is set when `/dev/dxg` and `librocdxg.so` exist.

### CPU / Thread Pools

- `UNSLOTH_CPU_THREADS` caps native CPU thread pools such as `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, and related variables when they are unset.
- Invalid values stop startup with a clear error.

## Provider Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Public key mismatch/decrypt failure | Frontend held an old RSA public key | Refresh client/page and re-enter key. |
| Custom provider test says model ID required | Custom providers use chat-completion probe | Provide a concrete model ID. |
| `/models` unsupported or empty | Provider uses curated list or custom proxy | Use registry suggestions/manual model ID; verify base URL. |
| Gemini/custom proxy model list filtered unexpectedly | Provider type/base host mismatch | Check native Gemini host vs proxy and choose provider type accordingly. |
| Chat provider works in UI but agent fails | Agent uses local `/v1` Studio API, not external provider directly | Confirm Studio has selected provider/model and client bearer key is valid. |

## RAG and Data Recipe Failures

RAG:

- `503`: sqlite-vec unavailable.
- `400 unsupported file type`: extension not in allowed RAG config.
- `400 empty file`: upload had no bytes.
- `404 document file not available`: DB row exists but stored file is absent.
- `401 invalid or expired token`: preview signed URL expired or mismatched; mint a new file URL.

Data recipes:

- HF seed inspect requires a repo id like `org/repo`; bad split/subset/token can produce `422`.
- Unstructured uploads support configured text/document extensions and can fail if no extractable text exists.
- Recipe jobs require columns and valid `execution_type` (`preview` or `full`).
- Publishing requires a completed full run with publishable artifact path, repo id, description, and token when needed.

## Startup/Shutdown and Logs

- Startup writes session logs and enables fault handlers before heavy imports so import-time failures leave evidence.
- Graceful shutdown tries to stop inference orchestrator, export subprocess, training backend, llama-server, Cloudflare tunnel, and child processes.
- Ctrl+C should trigger graceful shutdown; a second signal may force quit if shutdown stalls.
- If a server was launched by `unsloth studio run` and model load fails, the wrapper should tear down the server and children rather than orphan them.

## Escalation Checklist

Escalate from safe checks to mutating fixes only after explaining impact:

1. Inspect env/flags/path/help with `studio_preflight.py`.
2. Query health/status routes with user-provided API key if needed.
3. Retry launch with corrected flags/root.
4. Rerun `unsloth studio setup` or public installer/update if assets/runtime are missing.
5. Trigger `/api/llama/update` only for confirmed stale/unsupported llama.cpp and with approval.
6. Revoke/rotate keys after exposure.
7. Uninstall/reinstall only when setup state is corrupt and the user agrees.
