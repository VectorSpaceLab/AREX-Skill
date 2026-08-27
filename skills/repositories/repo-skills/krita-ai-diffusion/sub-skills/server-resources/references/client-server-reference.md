# Client and Server Reference

Krita AI Diffusion can generate through three broad server modes:

- Managed local ComfyUI installed/started by the plugin.
- External local or remote ComfyUI supplied by the user.
- Cloud image-generation service accessed through the plugin's cloud client.

This skill treats all live server operations as side-effecting. Do not start,
install, download, upgrade, uninstall, upload LoRAs, call cloud APIs, or run
generation unless the user explicitly requests that action and accepts the
runtime/cost consequences.

## Important classes

- `ai_diffusion.backend.comfy_client.ComfyClient`: HTTP/WebSocket client for a
  ComfyUI server. Connects, discovers models, submits workflows, uploads image
  and LoRA data, receives progress/output, and handles interruption.
- `ai_diffusion.backend.cloud_client.CloudClient`: HTTP client for the cloud
  service. Requires service URL/authentication and can report cloud-specific
  job states and errors.
- `ai_diffusion.backend.client.ClientModels`: discovered checkpoints, LoRAs,
  control resources, upscalers, text encoders, VAEs, and helpers for resolving
  architecture-specific resources.
- `ai_diffusion.backend.server.Server`: managed ComfyUI installation lifecycle:
  `check_install`, `install`, `download`, `start`, `stop`, `verify`,
  `fix_models`, `upgrade`, and `uninstall`.
- `ai_diffusion.settings.ServerMode`: `undefined`, `managed`, `external`,
  `cloud`.
- `ai_diffusion.settings.ServerBackend`: `cpu`, `cuda`, `mps`, `directml`,
  `xpu`, `rocm` with platform-dependent support.

## Server state model

`ServerState` values include install and runtime states such as:

```text
not_installed, missing_resources, installing, stopped, starting, running,
stopping, update_required, unsupported, error
```

Exact transitions depend on local filesystem state, Python availability,
resource catalog version, and backend. For managed server tasks, first inspect
state without mutating. Only then decide whether `install`, `download`,
`upgrade`, `verify`, `fix_models`, or `uninstall` is appropriate.

## URL normalization

Use the bundled helper to normalize user input into HTTP/WebSocket endpoints:

```bash
python sub-skills/server-resources/scripts/check_server_resources.py --parse-url localhost:8188
```

Typical output includes an HTTP URL and a WebSocket URL. If a user provides a
bare host/port, prefer normalizing rather than hand-building paths.

## Managed server safety policy

Before running managed server methods, ask or confirm:

- Target server directory and whether it may be created or mutated.
- Backend (`cuda`, `cpu`, `mps`, `directml`, `xpu`, `rocm`) and hardware/driver
  availability.
- Whether network downloads are allowed and how large downloads may be.
- Whether model files may be downloaded, verified, repaired, or deleted.
- Whether an existing server install may be upgraded or uninstalled.
- Port selection and whether an existing process may be stopped.

Use read-only checks and parse error messages before destructive recovery.

## Cloud safety policy

Cloud mode requires an access token and can incur cost. Do not send prompts,
images, LoRAs, or workflow JSON to the cloud service unless the user explicitly
requests cloud generation/debugging and authorizes use of credentials/service.
For insufficient funds or auth failures, report the state and remediation
without retry loops that could incur repeated requests.

## Common server errors parsed by code

`server.parse_common_errors` recognizes several frequent startup/install
patterns, including:

- Port already in use / bind address failures.
- Missing system libraries or DLLs.
- Python/runtime launch failures.
- Installer/git/download failures.
- Model/resource verification failures.

If startup output is long, preserve the relevant tail and map it to the closest
known failure before recommending reinstall.

## Native evidence anchors

- Server lifecycle and installer behavior are covered by `tests/test_server.py`,
  but install/download/uninstall tests are unsafe by default.
- `tests/test_client.py` covers live Comfy client behavior but requires a running
  managed server and model resources.
- `tests/test_workflow.py` can exercise local/cloud generation but requires
  live backends and is not part of the safe default verification scope.
