---
name: dream-textures
description: "Use and troubleshoot the Dream Textures Blender add-on for Stable
  Diffusion image generation, texture projection, render passes, model setup,
  and backend APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Dream Textures Repo Skill

Dream Textures is a Blender add-on that integrates Stable Diffusion/Diffusers workflows into Blender for prompt-based image generation, seamless textures, inpainting/outpainting, AI upscaling, 3D texture projection, Cycles render-pass processing, and node-based scene generation.

Load this root skill when a task names Dream Textures, Blender Stable Diffusion, Dream panel generation, Project Dream Texture, Dream Textures render pass, `dream_textures` backend/API objects, or the repository's model/dependency setup. Then route to the smallest sub-skill below.

## Quick setup facts

- Public project name: Dream Textures.
- Blender add-on package/import name: `dream_textures`.
- Version baseline for this skill: `0.4.1` from the source snapshot in [repo-provenance.md](references/repo-provenance.md).
- Minimum Blender version in `bl_info`: `3.1.0`.
- Ordinary users should prefer an official prebuilt release archive. For source/developer installs, place the add-on folder as `dream_textures`, then install exactly one matching platform/backend requirements file into the add-on's `.python_dependencies` directory using Blender's Python or the add-on Developer Tools; the setup sub-skill has the step-by-step workflow.
- Full local generation requires Blender, model weights, matching dependencies, and sufficient memory/VRAM. DreamStudio workflows require a valid API key and network access.

Minimal visibility checks:

```bash
python scripts/check_dream_textures_environment.py --help
python scripts/check_dream_textures_environment.py --addon-dir /path/to/dream_textures
```

The helper is a safe diagnostic only; it does not prove full Blender generation.

## Route by task

| User task or symptom | Read this |
| --- | --- |
| Install/enable the add-on, decide release vs source install, choose CUDA/ROCm/MPS/DirectML requirements, diagnose `.python_dependencies`, manage Hugging Face or DreamStudio credentials, download/link/import models, or fix checkpoint/model-type mismatch | [setup-and-models](sub-skills/setup-and-models/SKILL.md) |
| Generate images/textures from prompts, use negative prompts, source-image modify/depth modes, inpaint/outpaint, seamless axes, ControlNet from images, prompt history JSON, or AI upscaling | [generation-workflows](sub-skills/generation-workflows/SKILL.md) |
| Project a generated texture onto selected mesh faces, use viewport depth/color, bake projected UVs, enable the Cycles Dream Textures render pass, connect the compositor socket, use the Dream Textures render engine/node tree, or create scene annotation maps | [scene-integration](sub-skills/scene-integration/SKILL.md) |
| Implement or debug a custom backend, inspect `GenerationArguments`, task dataclasses, `Backend.generate`, `DiffusersBackend`, schedulers, model-type compatibility, generator `Future` callbacks, or source-level import errors | [backend-and-api](sub-skills/backend-and-api/SKILL.md) |
| The symptom spans several areas or you need first-triage guidance | [root troubleshooting](references/troubleshooting.md) |

## Common decision points

- **Model family before prompt debugging**: prompt/image-to-image uses prompt-to-image models; inpaint/outpaint uses inpainting models; depth/projection/render-pass depth input uses depth models; upscaling uses the Stable Diffusion x4 upscaler; ControlNet conditioning also needs matching ControlNet model entries.
- **Scene versus image workflow**: Image Editor and Shader Editor generation route to `generation-workflows`; 3D Viewport projection, Cycles pass, and render-engine node trees route to `scene-integration`.
- **Setup versus runtime**: missing packages, empty model list, checkpoint config, Hugging Face tokens, and DreamStudio keys route to `setup-and-models`; model/task validation and scheduler/source internals route to `backend-and-api` only when the user asks about API behavior or code.
- **Verification limits**: this skill's bundled scripts are safe planners/diagnostics. They intentionally do not install packages, open Blender, download models, contact services, or run Stable Diffusion.

## Repo-level references and script

- [repo-provenance.md](references/repo-provenance.md) records the source commit, version, dirty-state baseline, and evidence paths used to create this skill. Read it before deciding whether to refresh the skill.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for the managed repo-skills router.
- [troubleshooting.md](references/troubleshooting.md) gives root triage for install/runtime/model/backend symptoms and routes to deeper sub-skill troubleshooting.
- [check_dream_textures_environment.py](scripts/check_dream_textures_environment.py) safely reports add-on layout, optional Python module visibility, Blender executable visibility, and torch backend facts.

## Do not do these from this skill

- Do not tell future agents to open, run, or edit files from an original Dream Textures checkout as part of normal runtime use. Use the bundled references and scripts here.
- Do not install all requirement variants or mutate a user's Blender Python environment without explicit approval.
- Do not claim CUDA/ROCm/MPS/DirectML, DreamStudio, model-download, or full Blender generation verification unless those checks were run in the user's actual environment.
