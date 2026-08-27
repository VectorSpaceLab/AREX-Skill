---
name: dreamcraft3d
description: "Use DreamCraft3D for image-conditioned 3D generation, staged
  optimization, texture boosting, export, and CUDA troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DreamCraft3D

Use this repo skill when a user is working with DreamCraft3D, a CUDA-first research checkout for hierarchical 3D generation from a reference image using staged geometry sculpting and bootstrapped texture refinement.

This skill is self-contained operating guidance: it distills commands, configs, data layouts, model artifacts, and troubleshooting from the repository. It does not include model weights or run training by itself.

## Start here

1. Check whether the user's checkout matches this skill baseline in [references/repo-provenance.md](references/repo-provenance.md).
2. Read [references/config-reference.md](references/config-reference.md) for the main CLI, registry names, canonical configs, and shared artifact conventions.
3. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting CUDA, dependency, model-artifact, image/config, and output failures.
4. Run [scripts/dreamcraft3d_static_check.py](scripts/dreamcraft3d_static_check.py) for a safe checkout/skill/config preflight; it does not import heavy ML packages or launch training.

## Sub-skill routes

- Use [sub-skills/image-preparation/SKILL.md](sub-skills/image-preparation/SKILL.md) for reference-image preprocessing, `_rgba/_depth/_normal` sidecars, recentering, caption sidecars, and image-load assertions.
- Use [sub-skills/generation-pipeline/SKILL.md](sub-skills/generation-pipeline/SKILL.md) for the four canonical stages, `launch.py` commands, OmegaConf overrides, checkpoint chaining, and stage-specific troubleshooting.
- Use [sub-skills/bootstrapped-texture/SKILL.md](sub-skills/bootstrapped-texture/SKILL.md) for optional Zero123++ multiview generation, DreamBooth/LoRA texture boosting, Stable Zero123/Stable Diffusion/DeepFloyd/Omnidata artifacts, and Janus-problem mitigation.
- Use [sub-skills/export-and-evaluation/SKILL.md](sub-skills/export-and-evaluation/SKILL.md) for mesh export, OBJ/MTL/textures, output directory summaries, validation/test assets, metrics, and progress-video utilities.
- Use [sub-skills/interfaces-and-monitoring/SKILL.md](sub-skills/interfaces-and-monitoring/SKILL.md) for installation/backend triage, Docker/NVIDIA container guidance, Gradio launch/watch behavior, GPU memory checks, and safe environment diagnostics.

## Installation and runtime route

DreamCraft3D is operated from a source checkout rather than an installable package distribution. For setup questions, route to `interfaces-and-monitoring`: it covers the documented Python, CUDA, PyTorch, Docker, NVIDIA Container Toolkit, compiled extension, and model-artifact requirements. A minimal public readiness check is to confirm the checkout has `launch.py`, `requirements.txt`, the four `configs/dreamcraft3d-*.yaml` files, and visible CUDA hardware before attempting full training.

## Minimal operating checks

From a DreamCraft3D checkout, use the bundled static checker when you need a cheap preflight:

```bash
python <skill-dir>/scripts/dreamcraft3d_static_check.py --repo-root . --json
```

For a full operator preflight with GPU/model-path warnings, route to `interfaces-and-monitoring` and use its environment checker.

## Canonical workflow at a glance

1. Prepare or validate a single image family: `<stem>_rgba.png`, `<stem>_depth.png`, and `<stem>_normal.png`.
2. Run coarse NeRF with `configs/dreamcraft3d-coarse-nerf.yaml`.
3. Run coarse NeuS with `configs/dreamcraft3d-coarse-neus.yaml` and `system.weights=<coarse-nerf-last.ckpt>`.
4. Run geometry refinement with `configs/dreamcraft3d-geometry.yaml` and `system.geometry_convert_from=<coarse-neus-last.ckpt>`.
5. Run texture refinement with `configs/dreamcraft3d-texture.yaml` and `system.geometry_convert_from=<geometry-last.ckpt>`.
6. Export a mesh from the final trial's `configs/parsed.yaml` and `ckpts/last.ckpt` using `system.exporter_type=mesh-exporter`.

Use the generation-pipeline command builder instead of composing long shell commands from memory.

## Required runtime assumptions

DreamCraft3D's actual generation path requires a CUDA-capable NVIDIA GPU, compatible PyTorch CUDA wheels, GPU rendering/ML extensions, and large pretrained model artifacts. Static checks, command builders, and output summarizers can run without those dependencies, but they are not proof that full training or export succeeded.

## Import and verification status

This skill was produced for a no-import run. Do not assume it has been installed into the managed live repo-skills library. The verification artifacts for this production run record that full CUDA native training/export was not executed.
