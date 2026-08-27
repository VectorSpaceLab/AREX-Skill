---
name: worldgen
description: "Guides WorldGen workflows for generating 3D scenes from text,
  images, panoramas, or the interactive demo, including Gaussian-splat and mesh
  outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WorldGen

WorldGen turns text prompts, source images, or equirectangular panoramas into
3D scenes. The main pipeline generates a 360 panorama, predicts depth, and
converts the result into a Gaussian splat or an Open3D mesh; the bundled viewer
adds browser-based free-view exploration and novel-view export.

## Install and import check

WorldGen targets Python 3.11 and a CUDA-capable PyTorch environment for real
scene generation:

```bash
python -m pip install -e .
python scripts/check_worldgen_env.py --demo-help
```

The package also needs the external DA-2/PyTorch3D/Nunchaku/Open3D/Viser stack
shown in [`references/troubleshooting.md`](references/troubleshooting.md). Keep
those compiled dependencies on a compatible Python, torch, and CUDA ABI.

## Route by task

- **Generate from text, an image, or a panorama; select splat or mesh output**:
  use [`sub-skills/scene-generation/SKILL.md`](sub-skills/scene-generation/SKILL.md).
- **Run the interactive browser viewer or save novel views**: use the same
  scene-generation route and [`references/cli-reference.md`](references/cli-reference.md).
- **Inspect constructor, method, tensor, and output contracts**: read
  [`references/api-reference.md`](references/api-reference.md).
- **Diagnose installation, CUDA, model downloads, optional Sharp/inpainting, or
  viewer failures**: read [`references/troubleshooting.md`](references/troubleshooting.md)
  and then the scene-generation troubleshooting reference.
- **Check freshness against the source checkout**: read
  [`references/repo-provenance.md`](references/repo-provenance.md).

## Common starting points

- Begin with the scene-generation sub-skill for `WorldGen(mode="t2s")`,
  `WorldGen(mode="i2s")`, `_generate_world(pano_image)`, or `return_mesh=True`.
- Use `scripts/check_worldgen_env.py` before any long model download. It checks
  imports, public signatures, and a tiny CUDA allocation without loading weights.
- Use `scripts/worldgen_demo.py --help` to inspect the self-contained interactive
  launcher. It does not depend on the original repository checkout.
- Treat `use_sharp=True` and `inpaint_bg=True` as optional experimental branches;
  validate the default splat or mesh path first.

## Shared references and scripts

- [`references/api-reference.md`](references/api-reference.md) contains verified
  signatures, mode rules, output types, and lower-level conversion helpers.
- [`references/cli-reference.md`](references/cli-reference.md) documents the
  bundled demo flags, output files, viewer behavior, and safe preflight.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers
  install/import, CUDA, VRAM, model access, input validation, and viewer errors.
- [`scripts/check_worldgen_env.py`](scripts/check_worldgen_env.py) runs the
  read-only import/API/CUDA smoke check.
- [`scripts/worldgen_demo.py`](scripts/worldgen_demo.py) is the bundled,
  self-contained Viser launcher adapted from the repo's public demo workflow.

## Boundaries

This is a runtime user skill for WorldGen's generation and visualization
surface. It does not cover model training, release engineering, repository
maintenance, upstream DA-2/PyTorch3D development, or generic Open3D/Viser usage
without WorldGen. Optional Sharp and background-inpainting guidance is included
only as an explicitly unverified extension to the core generation route.
