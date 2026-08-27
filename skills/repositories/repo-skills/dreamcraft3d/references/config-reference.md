# DreamCraft3D Config Reference

## Purpose

Read this for cross-cutting DreamCraft3D CLI, registry, config, and artifact facts shared by multiple sub-skills.

## Main CLI

`launch.py` is the central launcher. It accepts:

| Argument | Meaning |
| --- | --- |
| `--config PATH` | Required YAML config path. |
| `--gpu IDS` | GPU ids to expose when `CUDA_VISIBLE_DEVICES` is not already set; default `0`. |
| `--train`, `--validate`, `--test`, `--export` | Mutually exclusive modes; exactly one is required. |
| `--gradio` | Gradio progress/logging mode. |
| `--verbose` | Debug logging. |
| `--typecheck` | Enables jaxtyping/typeguard import hook for `threestudio`. |

Unknown trailing arguments are OmegaConf overrides. Quote values that contain spaces:

```bash
system.prompt_processor.prompt="a ceramic lion" data.image_path="load/images/lion_rgba.png"
```

## Canonical configs

| Config | Stage role | Key components |
| --- | --- | --- |
| `dreamcraft3d-coarse-nerf.yaml` | First coarse stage | `implicit-volume`, `nerf-volume-renderer`, DeepFloyd guidance, Stable Zero123 3D guidance. |
| `dreamcraft3d-coarse-neus.yaml` | Coarse SDF refinement | `implicit-sdf`, `neus-volume-renderer`, `system.weights` from coarse NeRF. |
| `dreamcraft3d-geometry.yaml` | DMTet geometry | `tetrahedra-sdf-grid`, `nvdiff-rasterizer`, `system.geometry_convert_from` from coarse NeuS. |
| `dreamcraft3d-texture.yaml` | Texture refinement | fixed DMTet geometry, `stable-diffusion-bsd-guidance`, `system.geometry_convert_from` from geometry. |

All four use `single-image-datamodule` and `dreamcraft3d-system`.

## Registered names

Recognize these names in config values and tracebacks:

- Systems: `dreamcraft3d-system`, `zero123-system`.
- Data: `single-image-datamodule`, `random-camera-datamodule`.
- Geometry: `implicit-volume`, `implicit-sdf`, `tetrahedra-sdf-grid`.
- Renderers: `nerf-volume-renderer`, `neus-volume-renderer`, `nvdiff-rasterizer`.
- Guidance: `deep-floyd-guidance`, `stable-zero123-guidance`, `stable-diffusion-bsd-guidance`.
- Prompt processors: `deep-floyd-prompt-processor`, `stable-diffusion-prompt-processor`.
- Exporter: `mesh-exporter`.

## Shared artifact conventions

- Image family: `<stem>_rgba.png`, `<stem>_depth.png`, `<stem>_normal.png`, optional `<stem>_caption.txt`.
- Zero123 config: `load/zero123/sd-objaverse-finetune-c_concat-256.yaml`.
- Stable Zero123 checkpoint: config examples use `load/zero123/stable_zero123.ckpt`; code defaults also mention the hyphenated form.
- DMTet grids: `load/tets/32_tets.npz`, `load/tets/64_tets.npz`, `load/tets/128_tets.npz`.
- Default output root: `outputs`; Gradio output root: `outputs-gradio`.
- Trial checkpoint: `<trial-dir>/ckpts/last.ckpt`.
- Reproducible parsed config: `<trial-dir>/configs/parsed.yaml`.

## Full runtime versus safe helpers

Bundled scripts in this skill are safe planners/checkers. They do not replace:

- CUDA installation,
- PyTorch CUDA wheel verification,
- compiled extension builds,
- model checkpoint/cache acquisition,
- native DreamCraft3D training,
- mesh export from a real checkpoint.

Use them to decide whether a runtime action is ready, not to claim the action has completed.
