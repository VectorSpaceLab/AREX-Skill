---
name: launch-and-config
description: "Launch Stable Diffusion WebUI safely in UI, API, and API-only
  modes, choose configuration flags, and diagnose startup failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Launch and Config

Use this sub-skill when a task asks to start WebUI, enable the REST API, run API-only mode, set model/data paths, configure auth/TLS/CORS/subpath, reduce VRAM use, avoid launcher side effects, or diagnose Python/torch/xformers/checkpoint startup failures.

## Fast Start

1. Pick the server mode:
   - UI only: `python launch.py --ckpt <checkpoint.safetensors>`
   - UI plus API: `python launch.py --api --api-auth user:pass --ckpt <checkpoint.safetensors>`
   - API only: `python launch.py --nowebui --api-auth user:pass --ckpt <checkpoint.safetensors>`
2. Choose path flags before launch: `--data-dir`, `--models-dir`, `--ckpt`, `--ckpt-dir`, `--vae-dir`, `--embeddings-dir`, `--ui-settings-file`, and `--ui-config-file`.
3. Add network exposure flags deliberately: `--listen` or `--server-name`, `--port`, `--gradio-auth`, `--api-auth`, `--tls-keyfile`, `--tls-certfile`, `--subpath`, and only narrow `--cors-allow-origins` values.
4. Add hardware/performance flags from evidence: `--medvram`, `--medvram-sdxl`, `--lowvram`, `--lowram`, `--xformers`, `--opt-sdp-attention`, `--upcast-sampling`, `--no-half`, `--no-half-vae`, `--use-cpu`, or `--device-id`.
5. Diagnose startup with [troubleshooting.md](references/troubleshooting.md) before bypassing checks; `--skip-python-version-check`, `--skip-torch-cuda-test`, `--skip-install`, and `--skip-prepare-environment` hide symptoms and can leave dependencies unresolved.

## Bundled References

- [launch-and-installation.md](references/launch-and-installation.md): launch entry points, side effects, mode examples, wrapper behavior, and safe command patterns.
- [configuration.md](references/configuration.md): flag catalog by purpose, config files, environment variables, security posture, path strategy, and reverse-proxy setup.
- [troubleshooting.md](references/troubleshooting.md): failure signals and fixes for Python, torch/CUDA/xformers, missing checkpoints, downloads, auth/CORS/TLS/subpath, config freeze, and path mistakes.
- [extract_cli_flags.py](scripts/extract_cli_flags.py): self-contained AST helper that extracts `argparse` flags from a WebUI `modules/cmd_args.py` file without importing WebUI.

Example helper usage when auditing a checkout:

```bash
python sub-skills/launch-and-config/scripts/extract_cli_flags.py --source modules/cmd_args.py --format markdown
python sub-skills/launch-and-config/scripts/extract_cli_flags.py --source modules/cmd_args.py --format json
```

## Safe Defaults

- Do not expose a server with `--listen`, `--server-name 0.0.0.0`, `--share`, or `--ngrok` unless auth and network controls are explicit.
- Pair UI auth and API auth separately: `--gradio-auth` protects Gradio UI; `--api-auth` protects `/sdapi/v1/*` routes.
- Treat `--allow-code`, `--enable-insecure-extension-access`, `--disable-safe-unpickle`, and `--api-server-stop` as high-risk; use only for trusted local environments.
- Use `--no-download-sd-model` when startup must not fetch a fallback checkpoint; provide `--ckpt` or `--ckpt-dir` instead.
- Use `--disable-all-extensions` or `--disable-extra-extensions` while debugging launch failures from user extensions.

## Boundaries

- Route REST payload construction, endpoint semantics, and API smoke requests to `../api-automation/SKILL.md`.
- Route checkpoint, VAE, Lora, embedding, upscaler, hash, and asset layout details to `../assets-and-models/SKILL.md`.
- Route extension authoring, callback hooks, script templates, and extension install behavior beyond launch gating to `../extension-scripting/SKILL.md`.
- Route textual inversion, hypernetwork training, extras, face restoration, and postprocessing workflows to `../training-and-postprocessing/SKILL.md`.
