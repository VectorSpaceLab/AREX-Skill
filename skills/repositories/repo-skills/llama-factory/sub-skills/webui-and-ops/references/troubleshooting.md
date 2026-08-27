# Troubleshooting Web UI and Ops

## Missing or partial install

Symptoms:

- `llamafactory-cli` or `lmf` is not found.
- `ModuleNotFoundError: llamafactory`.
- `llamafactory-cli env` fails while importing `torch`, `transformers`, `datasets`, `accelerate`, `peft`, or `trl`.
- `llamafactory-cli webui` fails before printing a Gradio URL.

Actions:

1. Run `python sub-skills/webui-and-ops/scripts/llamafactory_sanity_check.py` to separate missing package metadata, import failures, missing CLI entry points, and optional web/API dependency gaps.
2. Confirm Python is `>=3.11`.
3. Install in an isolated environment with `pip install -e .`, or install the published package appropriate for the user's workflow.
4. Install platform-specific PyTorch first when CUDA/NPU/ROCm wheels are the failure source.
5. Re-run `llamafactory-cli help` before `env`; `env` imports heavier ML dependencies.

## Missing web/API dependencies

The full source metadata includes `gradio`, `fastapi`, `uvicorn`, and `sse-starlette`. Partial/source-only environments may not have them.

- Missing `gradio`: `webui` and `webchat` cannot construct Gradio Blocks. Install `gradio` in the active environment, or reinstall LLaMA Factory with its declared dependencies.
- Missing `matplotlib`: UI training plots or loss viewers can fail even if basic route discovery works.
- Missing `fastapi`, `uvicorn`, or `sse-starlette`: API routes are affected; this sub-skill only flags them and routes endpoint details to `inference-and-serving`.

## Port, proxy, and exposure issues

Symptoms:

- Browser cannot connect to `127.0.0.1:7860`.
- Gradio starts but is unreachable from another host or Docker host.
- Launch fails because the default port is occupied.
- Corporate proxy variables break local Gradio callbacks.

Actions:

- Bind explicitly with `GRADIO_SERVER_NAME=0.0.0.0 llamafactory-cli webui` for remote/container access.
- Use `GRADIO_IPV6=1` only when IPv6 is intended; it switches the default bind host to `[::]` and clears common proxy variables.
- Use `GRADIO_SHARE=1` only when an external share tunnel is acceptable.
- In Docker, publish `-p 7860:7860`; for API workflows also publish `-p 8000:8000`.
- If a port conflict occurs, stop the process currently using the port or configure Gradio's server port through Gradio-supported environment/launch settings in the runtime environment.

## Operational environment variables

| Variable | Use |
| --- | --- |
| `DISABLE_VERSION_CHECK=1` | Skips non-mandatory dependency version checks. Useful for temporary diagnosis, risky for production because incompatible versions can behave unexpectedly. |
| `RECORD_VRAM=1` | Enables VRAM recording in training callbacks. Useful for memory diagnostics. |
| `FORCE_TORCHRUN=1` | Forces distributed `torchrun` for training; Web UI sets it automatically for selected DeepSpeed configs. |
| `LLAMAFACTORY_VERBOSITY=DEBUG` | Increases logging detail. Valid logging names such as `DEBUG`, `INFO`, `WARN`, and `ERROR` are expected. |
| `USE_MODELSCOPE_HUB=1` | Prefer ModelScope for supported model/dataset downloads and UI model path defaults. |
| `USE_OPENMIND_HUB=1` | Prefer OpenMind/Modelers Hub for supported downloads and UI model path defaults. |
| `USE_V1=1` | Switches from default v0 launcher to experimental v1. Do not set for ordinary LlamaBoard v0 troubleshooting. |

The launcher also uses distributed variables such as `NNODES`, `NODE_RANK`, `NPROC_PER_NODE`, `MASTER_ADDR`, `MASTER_PORT`, `MAX_RESTARTS`, `RDZV_ID`, `MIN_NNODES`, and `MAX_NNODES` when `torchrun` is active. Route training topology details to `training-and-configs`.

## Experiment monitors

- W&B: set training config `report_to: wandb` and optionally `run_name`; provide `WANDB_API_KEY` in the environment or login beforehand.
- SwanLab: set `use_swanlab: true` and optionally `swanlab_run_name`, `swanlab_project`, `swanlab_workspace`, `swanlab_mode`, and `swanlab_api_key`; provide `SWANLAB_API_KEY` or use `swanlab login` when not putting a key in config. LlamaBoard can surface a SwanLab link during monitoring.
- MLflow/TensorBoard: select/report through training arguments where supported by the underlying trainer stack; route exact training config fields to `training-and-configs`.

Never paste API keys into public skill files, logs, or handoff reports. Prefer environment variables or prior CLI login for user secrets.

## Hard diagnostic scenarios

### Port/API key mismatch

If the user says the UI works but monitor links or API-backed widgets fail, distinguish three surfaces: Gradio Web UI port `7860`, API server port commonly `8000`, and monitor service authentication. Verify each service separately, confirm Docker port publishing, and check `WANDB_API_KEY`/`SWANLAB_API_KEY` only through presence/login status, not by printing secrets.

### Missing Gradio for Web UI

If `help` and `version` work but `webui` fails, suspect a partial install missing `gradio`. Run the sanity script, install or repair the declared GUI dependencies, and retry `llamafactory-cli webui` before changing model, dataset, or training YAML settings.
