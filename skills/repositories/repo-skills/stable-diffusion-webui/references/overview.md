# Stable Diffusion WebUI Overview

## Repository Shape

Stable Diffusion WebUI is an application-style repository rather than a conventional installable Python package. Its public surfaces are launcher entry points, Gradio UI behavior, `/sdapi/v1/*` FastAPI routes, built-in scripts/extensions, model asset discovery, and training/postprocessing utilities.

Key runtime areas:

| Area | Main evidence | Owning sub-skill |
| --- | --- | --- |
| Launch and configuration | `launch.py`, `webui.py`, shell/batch wrappers, `modules/cmd_args.py`, `modules/launch_utils.py` | `launch-and-config` |
| REST API automation | `modules/api/api.py`, `modules/api/models.py`, API tests | `api-automation` |
| Scripts and extensions | `modules/scripts.py`, `modules/script_callbacks.py`, `modules/scripts_postprocessing.py`, `extensions-builtin/*` | `extension-scripting` |
| Model assets | `modules/sd_models.py`, `modules/sd_vae.py`, `modules/modelloader.py`, Lora extension, upscalers | `assets-and-models` |
| Training and postprocessing | `modules/textual_inversion/`, `modules/hypernetworks/`, `modules/postprocessing.py`, postprocessing scripts | `training-and-postprocessing` |

## Cross-Sub-Skill Workflows

### API-Only Deployment With Assets

1. Use `launch-and-config` to select `--nowebui`, `--api-auth`, binding, port, TLS/subpath, and security flags.
2. Use `assets-and-models` to validate checkpoint, VAE, Lora, embedding, and upscaler directories before launch.
3. Use `api-automation` to probe read-only endpoints, construct generation payloads, and troubleshoot HTTP/API errors.
4. Return to `launch-and-config` if server exposure, auth, CORS, or reverse-proxy behavior is wrong.

### Extension That Adds Generation Behavior

1. Use `extension-scripting` to choose selectable vs always-on vs callback-only shape and scaffold files.
2. Use `api-automation` when the extension must expose API-visible script arguments or be called through `alwayson_scripts`.
3. Use `assets-and-models` when the extension consumes checkpoints, Lora, embeddings, or upscalers.
4. Use `launch-and-config` when extension loading is blocked by disable flags, unsafe access policy, or startup import errors.

### Textual Inversion Or Hypernetwork Workflow

1. Use `assets-and-models` to place embeddings/hypernetworks/checkpoints and confirm model discovery.
2. Use `training-and-postprocessing` to validate dataset/preprocessing/training plans and endpoint parameters.
3. Use `launch-and-config` for low-VRAM/device/server lifecycle decisions.
4. Use `api-automation` for request transport, auth, polling, and API error shape.

## Safety Model

- Launcher execution can install packages, clone extension repositories, download model dependencies, start a server, and initialize GPU/model state.
- Model loading can execute heavy tensor deserialization, consume significant VRAM/RAM, and trigger optional downloads.
- Extension scripts can run arbitrary Python at import time; `--allow-code` and insecure extension access are high-risk.
- API options and server-control endpoints mutate process or config state; always read current state and restore where possible.
- Training, upscaling, face restoration, and generation can be long-running and backend-dependent; validate plans and assets before execution.
