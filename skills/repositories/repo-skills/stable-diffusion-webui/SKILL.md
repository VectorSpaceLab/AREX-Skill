---
name: stable-diffusion-webui
description: "Use and maintain AUTOMATIC1111 Stable Diffusion WebUI workflows,
  including launch/configuration, REST API automation, extensions, model assets,
  LoRA, textual inversion, training, extras, and postprocessing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Stable Diffusion WebUI

Use this repo skill when the task names Stable Diffusion WebUI, AUTOMATIC1111, `launch.py`, `/sdapi/v1/*`, Gradio WebUI launch flags, WebUI extensions/scripts, checkpoints/VAEs/Lora/embeddings/upscalers, textual inversion, hypernetworks, Extras, or WebUI postprocessing workflows.

This skill is self-contained guidance distilled from the Stable Diffusion WebUI repository. It does not require the original checkout unless the user is explicitly auditing or modifying a checkout; bundled helper scripts are safe stdlib tools for source inspection, payload construction, extension scaffolding, and layout validation.

## Route By Task

| User task | Read |
| --- | --- |
| Start WebUI/API mode, choose launch flags, configure auth/CORS/TLS/subpath, avoid downloads, diagnose startup | [launch-and-config](sub-skills/launch-and-config/SKILL.md) |
| Build `/sdapi/v1/*` calls, create txt2img/img2img payloads, encode images, inspect script metadata, troubleshoot API 400/401/422 | [api-automation](sub-skills/api-automation/SKILL.md) |
| Write or debug WebUI scripts/extensions, callbacks, postprocessing scripts, preload hooks, extension metadata, Gradio component hooks | [extension-scripting](sub-skills/extension-scripting/SKILL.md) |
| Place or refresh checkpoints, VAEs, embeddings, hypernetworks, Lora/extra networks, upscalers, hashes, model directories | [assets-and-models](sub-skills/assets-and-models/SKILL.md) |
| Plan textual inversion or hypernetwork training, preprocessing-for-training, Extras upscaling, face restoration, postprocessing | [training-and-postprocessing](sub-skills/training-and-postprocessing/SKILL.md) |

## Common Entry Points

- `python launch.py --api --api-auth user:pass --ckpt <checkpoint.safetensors>` starts UI plus authenticated API; use `--nowebui` for API-only mode.
- `GET /sdapi/v1/samplers`, `/schedulers`, `/sd-models`, `/upscalers`, `/scripts`, and `/script-info` should precede generation payload construction.
- Checkpoint and VAE placement should be solved before API generation or training; model-list endpoints only show assets discovered by the running server.
- Custom scripts and extensions should keep WebUI imports inside generated extension files, not inside scaffolding tools.
- Textual inversion, hypernetwork training, face restoration, and upscaling are long-running/model-backed workflows; validate inputs before running them.

## Root References And Tools

- [repo-provenance.md](references/repo-provenance.md): source snapshot, evidence paths, dirty-state baseline, and refresh cues.
- [repo-routing-metadata.json](references/repo-routing-metadata.json): structured scenario metadata for DisCo managed routing.
- [overview.md](references/overview.md): capability map, repository shape, safety model, and cross-sub-skill workflow patterns.
- [troubleshooting.md](references/troubleshooting.md): cross-cutting install/import, optional dependency, backend, server, security, and workflow triage.
- [inspect_webui_source.py](scripts/inspect_webui_source.py): optional stdlib helper that summarizes CLI flags and API routes from a WebUI checkout without importing WebUI or loading models.

Example source-audit helper usage when the user is already working in a WebUI checkout:

```bash
python scripts/inspect_webui_source.py --repo . --json
```

## Safety Defaults

- Do not expose `--listen`, `--share`, `--ngrok`, broad CORS, server-stop endpoints, or insecure extension access without explicit auth and trust boundaries.
- Do not enable `--allow-code` or `--disable-safe-unpickle` unless the user accepts arbitrary-code or pickle risk.
- Do not run launcher modes that install packages, clone repositories, download models, start servers, load checkpoints, or initialize GPU state unless the user explicitly wants that action.
- Prefer `.safetensors` assets, explicit model paths, small API smoke payloads, and read-only metadata endpoints while diagnosing.

## Boundaries

- Use this skill for practical WebUI operation, automation, extension work, and asset/training workflow guidance.
- Use general Diffusers or ComfyUI skills instead when the task is about Python diffusion pipeline APIs or node-graph execution outside Stable Diffusion WebUI.
- Use a repository-maintenance skill in addition to this one when the user asks to edit WebUI source code, run native tests, or prepare pull-request changes.
