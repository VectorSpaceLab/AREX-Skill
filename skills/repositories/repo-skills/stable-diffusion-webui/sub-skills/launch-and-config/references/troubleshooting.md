# Troubleshooting

Start from the exact startup line. `launch.py` prints `Launching API server with arguments:` for `--nowebui` and `Launching Web UI with arguments:` otherwise. Match the observed failure to the sections below before adding skip flags.

## Quick Triage

1. Confirm mode: `--nowebui` means API-only; `--api` means API plus UI.
2. Confirm the process is using the intended Python and environment; wrapper scripts may create or activate a local venv.
3. Check whether the launcher is allowed to install packages or clone repositories. If `--skip-install` or `--skip-prepare-environment` is set, missing dependencies are expected.
4. Confirm a real checkpoint exists at `--ckpt`, in `--ckpt-dir`, or under the model directory; add `--no-download-sd-model` only when fallback downloads are forbidden.
5. For exposed servers, confirm both UI/API auth and proxy/TLS/subpath settings match the client URL.

## Python Version Mismatch

Failure signal:

- Startup prints `INCOMPATIBLE PYTHON VERSION`.
- Package installation fails with messages such as `RuntimeError: Couldn't install torch.`.
- Windows guidance says this app is tested with Python 3.10.6; Linux/macOS accept a wider 3.x minor range in the launcher check.

Fix:

- Prefer Python 3.10 for stable WebUI deployments.
- Recreate the wrapper venv after changing Python.
- Do not use `--skip-python-version-check` as a fix; it only suppresses the warning.
- If the wrapper used `python3` instead of `python3.10`, set `python_cmd` in `webui-user.sh` or `%PYTHON%` in `webui-user.bat`.

## Torch, CUDA, NPU, IPEX, and xformers Mismatch

Failure signals:

- `Torch is not able to use GPU; add --skip-torch-cuda-test ...`.
- `Couldn't install torch` from the launcher.
- `Cannot import xformers` or xformers version warning.
- Import/runtime errors after forcing `--force-enable-xformers`.

Fix:

- Pick one backend path and make `TORCH_COMMAND` match it before launch.
- Use `--skip-torch-cuda-test` only for CPU, NPU/IPEX paths, tests, or source inspection.
- Use `--xformers` only when the xformers package matches torch, Python, CUDA, and GPU capability.
- If xformers is stale, try `--reinstall-xformers` with a known-good `XFORMERS_PACKAGE`; if it still fails, remove xformers flags and use SDP/sub-quadratic attention instead.
- If torch is stale or wrong, use `--reinstall-torch` only in an environment where package mutation is acceptable.
- For Intel XPU, `--use-ipex` changes torch install behavior and skips the CUDA test.

## Missing Checkpoint or Accidental Model Download

Failure signals:

- `No checkpoints found. When searching for checkpoints, looked at:` followed by file and directory paths.
- `Can't run without a checkpoint. Find and place a .ckpt or .safetensors file into any of those locations.`
- `Checkpoint in --ckpt argument not found`.
- Unexpected download of fallback `v1-5-pruned-emaonly.safetensors` when no model is found.

Fix:

- Provide a concrete file with `--ckpt <file>` or a directory with `--ckpt-dir <dir>`.
- Use `--models-dir <dir>` when model family directories live outside `--data-dir`.
- Use `--no-download-sd-model` for air-gapped or reproducible startup, but expect startup to fail without a checkpoint.
- For VAE-specific issues, set `--vae-dir <dir>` or `--vae-path <file>`; route detailed asset layout to `../assets-and-models/SKILL.md`.
- For CI source inspection, do not run full launcher; use static helpers.

## Accidental Installs, Clones, or Extension Installer Runs

Failure signals:

- Startup begins `Installing torch`, `Installing requirements`, `Cloning ...`, or `Installing <extension>` unexpectedly.
- Network access starts during what was intended to be a local-only inspection.
- Extension installer errors appear before server startup.

Fix:

- Use static inspection when no runtime mutation is allowed.
- Add `--skip-prepare-environment` to skip all preparation, or `--skip-install` to skip pip installs and extension installers.
- Combine `--disable-extra-extensions` or `--disable-all-extensions` with `--skip-install` when debugging extension install failures.
- Set `REQS_FILE`, `TORCH_COMMAND`, package source env vars, and `INDEX_URL` explicitly in controlled environments.
- Remember that skipping preparation may leave missing repos/packages that later imports require.

## `--nowebui` vs `--api` Confusion

Failure signals:

- Client calls `/sdapi/v1/*` but receives 404 from a UI-only server.
- Operator expected no UI but launched Gradio.
- API-only server listens on `7861` instead of expected `7860`.

Fix:

- UI only: omit both `--api` and `--nowebui`.
- UI plus API: add `--api`; default UI port is the Gradio default unless `--port` is set.
- API only: add `--nowebui`; `--api` is not required; default port is `7861` unless `--port` is set.
- Use `--api-auth` for API routes in either API mode.
- Route payload and endpoint debugging to `../api-automation/SKILL.md`.

## `--listen` Without Auth

Failure signal:

- Launch command includes `--listen`, `--server-name 0.0.0.0`, `--share`, or `--ngrok` without `--gradio-auth` or `--api-auth`.

Fix:

- Add `--gradio-auth` for UI access and `--api-auth` for REST clients.
- Keep `--enable-insecure-extension-access` off for exposed servers.
- Keep `--allow-code`, `--disable-safe-unpickle`, and `--api-server-stop` off unless isolated and trusted.
- Restrict CORS to exact origins when browser clients need cross-origin API access.

## CORS, TLS, and Subpath Mistakes

Failure signals:

- Browser clients fail CORS preflight or cannot send credentials.
- Startup prints `Invalid path to TLS keyfile given`, `Invalid path to TLS certfile`, or `TLS setup invalid, running webui without TLS`.
- Reverse-proxy deployment loads HTML but API/docs/static paths are wrong.
- Client uses `/sdapi/v1/...` while server was launched behind a `--subpath` root.

Fix:

- Set both `--tls-keyfile` and `--tls-certfile`; one without the other is not enough.
- Use `--disable-tls-verify` only for self-signed/private certificates.
- Set `--subpath <mount>` without a leading slash, then have the proxy preserve or rewrite paths consistently.
- For API-only mode with `--subpath sdwebui`, clients normally call through the proxy at `/sdwebui/sdapi/v1/...`.
- Use comma-separated `--cors-allow-origins` without spaces; prefer exact origins over regex.
- If the proxy terminates TLS, omit app TLS and secure the upstream network separately.

## Unsafe Code and Extension Access Flags

Failure signals:

- Command contains `--allow-code`, `--enable-insecure-extension-access`, `--disable-safe-unpickle`, or `--api-server-stop` on a non-local server.
- Extension tab or custom scripts are reachable from remote clients.

Fix:

- Remove unsafe flags for public or shared instances.
- Use `--disable-extra-extensions` during incident response.
- Use `--disable-all-extensions` if built-in extensions are also suspect.
- Prefer safetensors checkpoints and leave safe unpickle checks enabled.

## Config Freeze or Restricted Settings

Failure signals:

- Settings changes through UI/API fail silently or report disabled/restricted settings.
- Errors mention `changing settings is disabled`, `settings in section ... are frozen`, `this setting is frozen`, or directory config is restricted.

Fix:

- Inspect launch flags: `--freeze-settings`, `--freeze-settings-in-sections`, `--freeze-specific-settings`, and `--hide-ui-dir-config`.
- Remove or narrow freeze flags for mutable deployments.
- For API changes, remember some options are marked `restrict_api=True` and cannot be changed through API.
- If startup warns `bad setting value`, fix or remove the settings JSON selected by `--ui-settings-file`.

## Path Layout Mistakes

Failure signals:

- Checkpoints, VAEs, embeddings, styles, localizations, or output paths are not found after changing `--data-dir` or `--models-dir`.
- Gradio cannot serve files outside allowed paths.
- UI hides directory config fields.

Fix:

- Decide whether `--data-dir` should own all mutable app state or whether `--models-dir` should point to shared model storage.
- Use explicit `--ckpt`, `--ckpt-dir`, `--vae-dir`, and `--embeddings-dir` rather than assuming defaults.
- Add only required file-serving roots with repeated `--gradio-allowed-path`.
- Remove `--hide-ui-dir-config` if operators must edit output/temp directories in the UI.
- Route detailed model/asset placement to `../assets-and-models/SKILL.md`.

## Low VRAM Startup or Generation Failures

Failure signals:

- Out-of-memory during model load or first generation.
- NaNs or black images from VAE.
- SDXL model loads but exhausts memory during generation.

Fix:

- Try `--medvram` first; use `--lowvram` when the speed trade-off is acceptable.
- For SDXL, try `--medvram-sdxl`.
- Add `--no-half-vae` or `--upcast-sampling` for precision-related VAE/sampling failures.
- Use `--opt-sdp-attention`, `--opt-sdp-no-mem-attention`, or `--opt-sub-quad-attention` as alternatives to xformers.
- Lower runtime generation parameters through UI/API; route payload tuning to `../api-automation/SKILL.md`.

## Diagnostic Commands That Avoid Full Startup

Use the bundled static helper to inspect CLI flags:

```bash
python sub-skills/launch-and-config/scripts/extract_cli_flags.py --source modules/cmd_args.py --format markdown
```

If a full runtime command is necessary, prefer a minimal debug profile first:

```bash
python launch.py --ui-debug-mode --skip-torch-cuda-test --disable-all-extensions --log-startup
```

Do not run full startup in environments where package installs, git clones, model downloads, extension installers, GPU initialization, or checkpoint loading are prohibited.
