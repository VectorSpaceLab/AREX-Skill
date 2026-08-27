# Launch and Installation

This repository is a Gradio application checkout. It is not a conventional installable Python package, and the launcher can create virtual environments, install packages, clone dependency repositories, download model-adjacent assets, run extension installers, and initialize GPU/model state.

## Entry Points

| Entry point | Use for | Behavior |
| --- | --- | --- |
| `python launch.py ...` | Cross-platform direct launch from an already prepared checkout | Parses CLI flags, optionally prepares the environment, then calls `webui.py`. |
| `./webui.sh ...` | Linux/macOS wrapper | Sources `webui-user.sh`, may create/activate `venv`, detects GPU hints, sets launcher env vars, then runs `launch.py`. |
| `webui-user.sh` | Linux/macOS local overrides | Store `COMMANDLINE_ARGS`, `python_cmd`, `venv_dir`, `TORCH_COMMAND`, `REQS_FILE`, `LAUNCH_SCRIPT`, and related env overrides here. |
| `webui.bat` / `webui-user.bat` | Windows wrapper and overrides | Creates/activates `%VENV_DIR%`, uses `%COMMANDLINE_ARGS%`, then runs `launch.py`. |
| `webui-macos-env.sh` | macOS defaults loaded by `webui.sh` | Sets MPS fallback and CPU-oriented flags; change `webui-user.sh` instead of editing this file. |
| `webui.py` | Internal server entry point | Selects API-only mode when `--nowebui` is present; otherwise launches the Gradio UI. |

Prefer `python launch.py` in documented agent commands because wrapper scripts are platform-specific. Prefer wrapper configuration files for humans who already use the app locally.

## Launcher Side Effects

`launch.py` delegates to `modules/launch_utils.py`. Unless suppressed, startup can:

- Check Python version and print an incompatible-version warning.
- Install or reinstall `torch`, `torchvision`, `clip`, `open_clip`, `xformers`, `ngrok`, and `requirements_versions.txt` packages.
- Clone dependency repositories into `repositories/` for assets, Stable Diffusion, SDXL, k-diffusion, and BLIP.
- Run `install.py` for enabled extensions.
- Perform torch CUDA availability checks.
- Check for application updates or update extensions when requested.
- Load model lists, scripts, upscalers, extra networks, and a checkpoint at startup.

Use these flags only when their trade-off is understood:

| Flag | Effect | Caveat |
| --- | --- | --- |
| `--skip-prepare-environment` | Skips all environment preparation. | Also skips installs/clones/checks that may be required for a fresh checkout. |
| `--skip-install` | Prevents pip package installs and extension installers. | Missing packages remain missing; does not skip git clones or all checks. |
| `--skip-python-version-check` | Suppresses the version warning. | Does not make unsupported Python compatible with torch wheels. |
| `--skip-torch-cuda-test` | Skips the CUDA availability assertion. | Useful for CPU/test environments; hides GPU setup failures. |
| `--skip-version-check` | Skips torch/xformers version checks. | Can mask incompatible xformers or torch versions. |
| `--no-download-sd-model` | Prevents fallback SD1.5 checkpoint download when no model is found. | Startup still needs a checkpoint unless using model-free debug/test paths. |
| `--do-not-download-clip` | Avoids CLIP download if checkpoint lacks CLIP. | Generation may fail with checkpoints that need external CLIP. |
| `--dump-sysinfo` | Writes limited sysinfo and exits. | Still enters launcher code; use in an environment where imports are safe. |

## Server Modes

### UI Only

Use when a browser UI is needed and REST automation is not required.

```bash
python launch.py --ckpt <checkpoint.safetensors> --port 7860
```

`webui.py` calls `webui()` when `--nowebui` is absent. Without `--api`, only UI-related routes and internal progress/UI APIs are added.

### UI plus REST API

Use when a user needs the Gradio UI and an automation client needs `/sdapi/v1/*`.

```bash
python launch.py \
  --api \
  --api-auth user:strong-password \
  --gradio-auth user:strong-password \
  --ckpt <checkpoint.safetensors> \
  --port 7860
```

`--api` makes WebUI create the REST `Api` object after Gradio launch. Use the `api-automation` sub-skill for payload construction and endpoint behavior.

### API Only (`--nowebui`)

Use for headless automation, reverse proxies, or services that do not need a Gradio UI.

```bash
python launch.py \
  --nowebui \
  --api-auth user:strong-password \
  --ckpt <checkpoint.safetensors> \
  --port 7861
```

`--nowebui` calls `api_only()`, creates a FastAPI app without Gradio UI, and launches on `--port` or default `7861`. In this mode, `--api` is not required; `--nowebui` means API instead of UI.

### Fast UI Debug

Use for UI layout/debug tasks that do not need a model load.

```bash
python launch.py --ui-debug-mode --skip-torch-cuda-test --disable-all-extensions
```

`--ui-debug-mode` avoids normal model loading in initialization. It is not a substitute for a real generation smoke test.

### Test Server Behavior

`--test-server` appends safe test-oriented arguments if absent: `--api`, a tiny test checkpoint path, `--skip-torch-cuda-test`, and `--disable-nan-check`, then clears `COMMANDLINE_ARGS`. It is intended for repository tests and not for production deployment.

## Model Loading at Startup

Normal startup lists checkpoints and starts a background load of `shared.sd_model` unless `--skip-load-model-at-start` is set. The flag only takes effect with `--nowebui` according to the argument help. If startup must be fast and headless, combine API-only mode with explicit model path control:

```bash
python launch.py \
  --nowebui \
  --skip-load-model-at-start \
  --ckpt <checkpoint.safetensors> \
  --api-auth user:pass
```

For CI or source inspection where no real model should load, do not run the full launcher; use static helpers such as `scripts/extract_cli_flags.py` instead.

## Environment Variables Recognized by Launchers

| Variable | Used by | Purpose |
| --- | --- | --- |
| `COMMANDLINE_ARGS` | `modules/paths_internal.py`, wrappers | Appended to `sys.argv` before CLI parsing. |
| `TORCH_COMMAND` | `launch_utils.prepare_environment()` | Overrides the pip command used to install torch/torchvision. |
| `TORCH_INDEX_URL` | `launch_utils.prepare_environment()` | Sets default torch wheel index for generated `TORCH_COMMAND`. |
| `REQS_FILE` | `launch_utils.prepare_environment()` | Selects requirements file, default `requirements_versions.txt`. |
| `REQS_FILE_FOR_NPU` | `launch_utils.prepare_environment()` | Selects NPU requirements file. |
| `XFORMERS_PACKAGE` | `launch_utils.prepare_environment()` | Overrides the xformers package spec installed with `--xformers`. |
| `CLIP_PACKAGE`, `OPENCLIP_PACKAGE` | `launch_utils.prepare_environment()` | Override package sources for CLIP dependencies. |
| `GIT` | wrappers and launcher | Git executable for clone/version operations. |
| `INDEX_URL` | `run_pip()` | Adds an index URL to pip installs. |
| `WEBUI_LAUNCH_LIVE_OUTPUT` | `launch_utils.run()` | Prints subprocess output live when set to `1`. |
| `GRADIO_ANALYTICS_ENABLED` | launch/import path | Defaults to `False`. |
| `ACCELERATE` | wrappers | Uses `accelerate launch` when set to `True` and available. |
| `NO_TCMALLOC` | `webui.sh` | Disables Linux TCMalloc preload probing. |

## Wrapper Notes

- Linux/macOS `webui.sh` refuses root by default; passing `-f` to the wrapper permits root launch, but production deployments should prefer an unprivileged user.
- `webui.sh` defaults to `python3.10` when available, then falls back to `python3`.
- `venv_dir="-"` in `webui-user.sh` disables wrapper-managed virtualenv support.
- Windows `webui.bat` uses `%PYTHON%`, `%GIT%`, `%VENV_DIR%`, `%COMMANDLINE_ARGS%`, and optional `webui.settings.bat` before creating or activating a venv.
- macOS defaults include `--skip-torch-cuda-test --upcast-sampling --no-half-vae --use-cpu interrogate` and `PYTORCH_ENABLE_MPS_FALLBACK=1`.
