# Configuration

Use command-line flags for startup-critical behavior and JSON config files for UI/settings defaults. Path, server exposure, auth, TLS, CORS, extension access, and model-load behavior must be decided before launch.

## Where Configuration Lives

| File or input | Default role | Notes |
| --- | --- | --- |
| CLI flags | Startup, paths, server mode, security, hardware | Parsed in `modules/cmd_args.py`; many cannot be changed after launch. |
| `COMMANDLINE_ARGS` | Persistent wrapper flags | Appended to process args before parsing; useful in `webui-user.sh` / `webui-user.bat`. |
| `config.json` | Settings page values | Default path is under `--data-dir`; override with `--ui-settings-file`. |
| `ui-config.json` | UI component defaults and ranges | Default path is under `--data-dir`; override with `--ui-config-file`. |
| `styles.csv` or other `--styles-file` values | Prompt styles | Can be specified multiple times. |
| Auth file for `--gradio-auth-path` | UI login credentials | Same `username:password` or comma-delimited format as `--gradio-auth`. |

## Path Strategy

| Flag | Purpose | Use when |
| --- | --- | --- |
| `--data-dir <dir>` | Base path for user data, default model directory, config files, extensions, embeddings, outputs. | Isolate one deployment's mutable state. |
| `--models-dir <dir>` | Base path for model families; overrides model base derived from `--data-dir`. | Share model storage across multiple data dirs. |
| `--ckpt <file>` | Specific checkpoint file to add and load. | Pin a known checkpoint and avoid ambiguous fallback. |
| `--ckpt-dir <dir>` | Extra checkpoint search directory. | Store checkpoints outside the data/model base. |
| `--vae-dir <dir>` | VAE search directory. | Keep VAEs separate or shared. |
| `--embeddings-dir <dir>` | Textual inversion embeddings directory. | Use a shared embeddings collection. |
| `--hypernetwork-dir <dir>` | Hypernetwork directory. | Keep hypernetworks outside default models tree. |
| `--localizations-dir <dir>` | UI localization files. | Use custom translations. |
| `--ui-settings-file <file>` | Settings JSON path. | Run multiple instances with different settings. |
| `--ui-config-file <file>` | UI config JSON path. | Pin UI defaults/ranges per deployment. |
| `--gradio-allowed-path <path>` | Additional path Gradio may serve. | Expose explicit local files in UI; can be repeated. |

Default path derivation: `--data-dir` controls mutable user data; `--models-dir` overrides only model base; extension user area is under data dir; built-in extensions remain part of the application tree.

## Launch Mode Flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--api` | Launch REST API together with the Gradio UI. | Required for `/sdapi/v1/*` while UI is running. |
| `--nowebui` | Launch API instead of WebUI. | API-only; default port is `7861` when `--port` is omitted. |
| `--api-auth user:pass[,u2:p2]` | Basic auth for API routes. | Separate from UI auth. |
| `--api-log` | Log API requests. | Useful for debugging clients; may expose request paths/timing in logs. |
| `--api-server-stop` | Enable `/server-kill`, `/server-restart`, `/server-stop`. | High-risk; only for trusted lifecycle automation. |
| `--ui-debug-mode` | Launch UI quickly without normal model load. | For UI/debug, not generation validation. |
| `--test-server` | Configure test server arguments. | Intended for repository tests. |

## Network, Auth, TLS, CORS, and Proxy Flags

| Flag | Purpose | Safe guidance |
| --- | --- | --- |
| `--listen` | Bind Gradio/FastAPI to `0.0.0.0`. | Always pair with auth and network firewall/proxy controls. |
| `--server-name <host>` | Explicit bind host. | `0.0.0.0` is equivalent to public listening on all interfaces. |
| `--port <port>` | Server port. | Ports below 1024 may require elevated privileges. |
| `--gradio-auth user:pass[,u2:p2]` | UI basic auth. | Does not protect API unless `--api-auth` is also set. |
| `--gradio-auth-path <file>` | Read UI auth credentials from a file. | File lines use the same `username:password` format. |
| `--tls-keyfile <file>` and `--tls-certfile <file>` | Enable TLS when both are present. | If either path is invalid, startup reports TLS setup issues. |
| `--disable-tls-verify` | Allow self-signed certificates. | Useful for private TLS; clients may still need trust configuration. |
| `--cors-allow-origins <origins>` | Comma-separated CORS allowlist. | Avoid `*` for exposed servers; no spaces. |
| `--cors-allow-origins-regex <regex>` | Regex CORS allowlist. | Keep strict; regex mistakes can expose the API. |
| `--subpath <path>` | Root path for reverse proxy mounting. | Use with proxy path rewriting; omit leading slash in the flag value. |
| `--timeout-keep-alive <seconds>` | Uvicorn keep-alive timeout. | Increase behind slow proxies if idle disconnects occur. |
| `--share` | Gradio share URL. | Treat as non-local; require auth and avoid unsafe flags. |
| `--ngrok <token>` and `--ngrok-options <json>` | Ngrok tunnel. | Treat as internet exposure; prefer provider-side auth plus WebUI auth. |

Reverse-proxy API-only example:

```bash
python launch.py \
  --nowebui \
  --listen \
  --port 7861 \
  --subpath sdwebui \
  --api-auth apiuser:strong-password \
  --tls-keyfile <key.pem> \
  --tls-certfile <cert.pem> \
  --cors-allow-origins https://example.invalid \
  --ckpt <checkpoint.safetensors> \
  --no-download-sd-model \
  --disable-extra-extensions
```

Do not add `--enable-insecure-extension-access`, `--allow-code`, or `--api-server-stop` for this profile unless the network and clients are fully trusted.

## Security-Sensitive Flags

| Flag | Risk | Recommended posture |
| --- | --- | --- |
| `--allow-code` | Enables custom script execution from WebUI. | Keep off except in a trusted local development instance. |
| `--enable-insecure-extension-access` | Enables extensions tab even for non-local UI. | Keep off for `--listen`, `--share`, `--ngrok`, or custom public `--server-name`. |
| `--disable-safe-unpickle` | Disables PyTorch model safety checks. | Keep off; prefer safetensors assets. |
| `--api-server-stop` | Allows API clients to stop/restart/kill server. | Keep off unless lifecycle automation is authenticated and isolated. |
| `--gradio-allowed-path` | Allows Gradio to serve extra local files. | Add only minimal required paths. |
| `--listen`, `--share`, `--ngrok` | Exposes server beyond localhost. | Require `--gradio-auth` and/or `--api-auth`; avoid unsafe extension access. |

The application computes `webui_is_non_local` from `--share`, `--listen`, `--ngrok`, or `--server-name`. Extension access is disabled for non-local use unless explicitly overridden with `--enable-insecure-extension-access`.

## VRAM, Precision, and Backend Flags

| Flag | Effect | Trade-off |
| --- | --- | --- |
| `--medvram` | Memory optimizations with moderate speed cost. | Good first response for low VRAM. |
| `--medvram-sdxl` | Apply medvram optimization for SDXL models. | Targeted to larger SDXL models. |
| `--lowvram` | More aggressive memory saving. | Larger speed cost. |
| `--lowram` | Load checkpoint weights directly to VRAM instead of RAM. | Useful when system RAM is constrained. |
| `--no-half` | Avoid fp16 model conversion. | More memory; can fix precision issues. |
| `--no-half-vae` | Keep VAE out of fp16. | Common fix for black/NaN VAE outputs. |
| `--precision full|half|autocast` | Select evaluation precision. | Default is `autocast`. |
| `--upcast-sampling` | Upcast sampling for stability. | Similar stability to `--no-half` with less memory cost. |
| `--xformers` | Enable xformers attention and install package if needed. | Version/backend-sensitive. |
| `--force-enable-xformers` | Force xformers even if checks reject it. | High failure risk; do not use for bug reports. |
| `--opt-sdp-attention` | Prefer PyTorch scaled-dot-product attention. | Requires PyTorch 2.*. |
| `--opt-sdp-no-mem-attention` | Deterministic SDP without memory-efficient attention. | Requires PyTorch 2.*; can use more memory. |
| `--opt-sub-quad-attention` | Prefer sub-quadratic attention. | Tune chunk flags if needed. |
| `--sub-quad-q-chunk-size`, `--sub-quad-kv-chunk-size`, `--sub-quad-chunk-threshold` | Chunk sub-quadratic attention. | Use when VRAM spikes in attention. |
| `--use-cpu <modules...>` | Force named modules to CPU. | Slower; macOS defaults use `interrogate`. |
| `--use-ipex` | Use Intel XPU path. | Also skips torch CUDA test. |
| `--device-id <id>` | Select default CUDA device. | May need `CUDA_VISIBLE_DEVICES` set before launch. |
| `--disable-nan-check` | Skip NaN checks. | Useful for model-free CI; hides real generation failures. |

## Config Freeze and UI Restrictions

| Flag | Effect |
| --- | --- |
| `--freeze-settings` | Disables changing all settings globally. |
| `--freeze-settings-in-sections <ids>` | Freezes comma-delimited settings sections such as `saving-images` or `upscaling`. |
| `--freeze-specific-settings <keys>` | Freezes individual settings keys such as `samples_save` or `samples_format`. |
| `--hide-ui-dir-config` | Hides/restricts directory configuration fields. |

If API or UI changes to `/options` silently fail or report restricted/frozen settings, inspect these flags and the target key's section. Settings can also fail to load when `config.json` contains values with wrong types; startup prints `Warning: bad setting value` and recommends fixing or deleting the settings file.

## Extension Gating

| Flag | Effect |
| --- | --- |
| `--disable-all-extensions` | Prevents all extensions from running. |
| `--disable-extra-extensions` | Prevents user extensions except built-ins. |
| `--update-all-extensions` | Git-pulls enabled extensions at startup. |
| `--enable-insecure-extension-access` | Enables extension UI even in non-local mode. |

Use `--disable-extra-extensions` when isolating failures from user-installed extensions. Use `--disable-all-extensions` for a stricter startup baseline.

## CLI Flag Inventory Helper

Use the bundled helper to inspect the current checkout's parser without importing WebUI:

```bash
python sub-skills/launch-and-config/scripts/extract_cli_flags.py --source modules/cmd_args.py --format markdown
```

The helper extracts option strings, help text, defaults, choices, action, type, and nargs from static `parser.add_argument(...)` calls. It intentionally does not evaluate imported path defaults or execute the launcher.
