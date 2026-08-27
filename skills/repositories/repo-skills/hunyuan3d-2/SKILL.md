---
name: hunyuan3d-2
description: "Route Hunyuan3D-2 repo-specific shape, texture, service, and
  backend workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Hunyuan3D-2 Repo Skill

Use this repo skill when a task names Hunyuan3D-2, `hy3dgen`, Hunyuan3D-DiT, Hunyuan3D-Paint, Tencent Hunyuan image-to-3D/texture generation, the repository's FastAPI/Gradio/Blender integrations, or its CUDA texture extensions.

## Route by task

| User task | Read next |
| --- | --- |
| Generate a white/geometry mesh from one image, multiview images, mini/fast/turbo variants, FlashVDM, VAE, or shape export parameters | [sub-skills/shape-generation/](sub-skills/shape-generation/) |
| Texture a generated or existing mesh, use Hunyuan3D-Paint, clean/reduce meshes, diagnose rasterizer/renderer/UV failures | [sub-skills/texture-and-mesh/](sub-skills/texture-and-mesh/) |
| Launch or call the FastAPI server, Gradio UI, Blender add-on, REST payloads, asynchronous status polling, service ports | [sub-skills/services-and-integrations/](sub-skills/services-and-integrations/) |
| Install `hy3dgen`, choose PyTorch/CUDA, build `custom_rasterizer`/`mesh_processor`, plan model caches, verify backend readiness | [sub-skills/environment-and-model-setup/](sub-skills/environment-and-model-setup/) |

## Cross-cutting references

- [Repo provenance](references/repo-provenance.md) records source version, evidence paths, and staleness signals.
- [Troubleshooting](references/troubleshooting.md) summarizes cross-skill failure routing.
- [Routing metadata](references/repo-routing-metadata.json) is structured metadata for managed repo-skill routing.

## Operating rules

- Actual shape, texture, FlashVDM, and VAE generation are CUDA workflows in this skill. CPU-only dry-runs or imports validate guidance but do not prove generation.
- Full model examples may download large Hugging Face checkpoints and use substantial GPU time. Prefer dry-runs and backend checks until the user approves downloads/runtime or confirms the weights are cached.
- Runtime instructions are self-contained. Use bundled references/scripts for guidance; source file names in provenance are staleness evidence, not runtime dependencies.
- Keep verification artifacts outside this runtime skill. Do not copy usability cases or verification reports into this runtime directory.

## Quick safe checks

From a copied skill directory, these checks avoid model downloads:

```bash
python sub-skills/environment-and-model-setup/scripts/check_install.py --json
python sub-skills/shape-generation/scripts/generate_shape.py --preset base --image input.png --dry-run
python sub-skills/texture-and-mesh/scripts/texture_mesh.py --mesh mesh.glb --image input.png --dry-run
python sub-skills/services-and-integrations/scripts/request_api.py --image input.png --dry-run
```

Use real generation only after the environment and model-cache constraints are acceptable.
