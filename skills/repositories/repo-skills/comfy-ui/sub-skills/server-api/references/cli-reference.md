# CLI and Launch Reference

ComfyUI is launched with `python main.py` plus server, storage, frontend, and backend flags. There is no required console entry point assumption. Use this reference for server/API-facing flags; route model-path and detailed backend/VRAM decisions to `../../models-config/`.

## Minimal Launches

Local-only API/UI server:

```bash
python main.py --listen 127.0.0.1 --port 8188
```

LAN-accessible server on a chosen interface:

```bash
python main.py --listen 192.168.1.10 --port 8188
```

Listen on all IPv4 and IPv6 addresses:

```bash
python main.py --listen --port 8188
```

`--listen` without an argument expands to `0.0.0.0,::`. Treat that as exposed service configuration and pair it with network controls, TLS/reverse proxy, and careful CORS choices.

## Network and HTTP Flags

- `--listen IP`: listen address. Default is `127.0.0.1`. Accepts comma-separated addresses. Without a value, listens on all IPv4/IPv6 addresses.
- `--port PORT`: server port. Default is `8188`.
- `--tls-keyfile PATH` and `--tls-certfile PATH`: enable HTTPS only when both key and certificate are supplied.
- `--enable-cors-header [ORIGIN]`: adds CORS middleware. With no origin value, allows `*`. Prefer a specific origin for browser integrations.
- `--max-upload-size MB`: request upload size limit, default `100` MB.
- `--enable-compress-response-body`: gzip JSON/text responses when requested by the client.
- `--dont-print-server`: suppress server address output.
- `--verbose DEBUG|INFO|WARNING|ERROR|CRITICAL`: logging level. `--verbose` without value means `DEBUG`.
- `--log-stdout`: send normal process output to stdout rather than stderr.

Default behavior without `--enable-cors-header` uses origin-protection middleware that rejects cross-site browser requests to loopback when host and origin do not match. Enabling broad CORS disables that protection for matching requests, so avoid `*` on untrusted networks.

## Browser and Frontend Flags

- `--auto-launch`: open the browser automatically.
- `--disable-auto-launch`: prevent auto-launch even if other options would enable it.
- `--windows-standalone-build`: enables standalone conveniences and implies auto-launch.
- `--front-end-version OWNER/REPO@VERSION`: select bundled frontend provider/version. `latest` may require internet access to query/download frontend packages.
- `--front-end-root PATH`: use a local frontend directory and override `--front-end-version`.
- `--feature-flag KEY[=VALUE]`: set CLI-settable feature flags; repeatable. Bare keys become `true`; booleans and numbers are converted.
- `--list-feature-flags`: print known CLI feature flags as JSON and exit.

## Storage and User-Data Flags

- `--base-directory PATH`: base directory for models, custom nodes, input, output, temp, and user directories.
- `--output-directory PATH`: output directory override.
- `--temp-directory PATH`: temp directory override.
- `--input-directory PATH`: input directory override.
- `--user-directory PATH`: user directory override; must be an existing readable directory.
- `--multi-user`: enable per-user storage and user-aware `/users`, `/settings`, and `/userdata` behavior.
- `--database-url URL`: database URL. SQLite is the default. `sqlite:///:memory:` is accepted for ephemeral DB use.
- `--enable-assets`: enable asset routes, DB synchronization, and background scanning.
- `--extra-model-paths-config PATH ...`: load extra model path YAML files. Route details to `../../models-config/`.

When `--multi-user` is enabled, API clients should not assume that settings, user data, assets, or file listings are global. User identity can affect route results.

## Manager, Custom Node, and API-Node Controls

- `--enable-manager`: enable ComfyUI-Manager if its package is installed.
- `--disable-manager-ui`: disable manager UI/endpoints while allowing scheduled/background manager tasks.
- `--enable-manager-legacy-ui`: enable legacy manager UI and imply `--enable-manager`.
- `--disable-all-custom-nodes`: skip loading custom nodes.
- `--whitelist-custom-nodes NAME ...`: allow specific custom node folders while `--disable-all-custom-nodes` is active.
- `--disable-api-nodes`: disable hosted API nodes and prevent the frontend from communicating with the internet; also adds a stricter content-security-policy middleware.
- `--comfy-api-base URL`: base URL for the Comfy API used by API nodes. Default is `https://api.comfy.org`.

Use `--disable-all-custom-nodes` and then selectively whitelist while diagnosing startup crashes. Use `--disable-api-nodes` when workflows must stay fully local or when external-provider credentials should not be usable.

## Backend and Memory Flags Relevant to Server Launch

Detailed model/backend selection belongs in `../../models-config/`, but server operators often need these high-level launch controls:

- `--cuda-device IDS`: expose only selected CUDA/HIP/Ascend devices to the process.
- `--default-device ID`: choose default device while leaving others visible.
- `--cpu`: run everything on CPU; slow and not all optional acceleration stacks support this equally.
- `--gpu-only`, `--highvram`, `--lowvram`, `--novram`: mutually exclusive VRAM strategy flags.
- `--reserve-vram GB` and `--vram-headroom GB`: keep memory free for OS/other workloads or dynamic VRAM.
- `--enable-dynamic-vram`, `--disable-dynamic-vram`: control dynamic VRAM behavior.
- `--async-offload [NUM_STREAMS]`, `--disable-async-offload`, `--fast-disk`: offload strategy flags.
- `--directml [DEVICE]`, `--oneapi-device-selector SELECTOR`: non-CUDA backend selectors.
- `--preview-method none|auto|latent2rgb|taesd` and `--preview-size PX`: sampler preview behavior. Preview generation affects websocket binary frames.
- `--quick-test-for-ci`: quick CI mode.
- `--debug-hang`: dump stack traces on Ctrl-C to debug hangs.

If startup fails inside optional GPU/backend packages, simplify launch flags, disable custom/API nodes as needed, and verify the installed torch/backend stack before assuming the HTTP server is broken.

## Security Checklist

- Keep local automation on `127.0.0.1` unless remote access is required.
- Do not combine public listening, permissive CORS, and no authentication boundary on untrusted networks.
- Prefer a reverse proxy for production TLS, request limits, auth, and logs; ComfyUI’s TLS flags are useful but minimal.
- Keep API-node keys in request `extra_data` or environment-backed client code, not in workflows committed to source control.
- Use `--disable-api-nodes` for offline-only deployments.
- Use `--max-upload-size` appropriate to expected workflow assets.
- Avoid `/internal/*` for external automation.
