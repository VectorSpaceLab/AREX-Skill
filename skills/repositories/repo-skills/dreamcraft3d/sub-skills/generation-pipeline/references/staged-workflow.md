# DreamCraft3D Staged Workflow

## Purpose

Read this when constructing or debugging the canonical DreamCraft3D command sequence. This reference distills the repository quickstart and config semantics so future agents do not need to reopen source documentation.

## Prerequisites

Before launching a stage, verify:

- You are in a DreamCraft3D checkout with `launch.py`, `configs/`, `threestudio/`, `load/images/`, `load/tets/`, and model artifact directories.
- The image path points to a preprocessed `_rgba.png` file.
- Required sidecars exist: `_depth.png` for the coarse configs, `_normal.png` when a config enables normal supervision.
- CUDA, PyTorch CUDA wheels, compiled renderers, and diffusion model checkpoints/caches are available.
- The prompt is shell-quoted and also passed as an OmegaConf override.

## Launch CLI facts

`launch.py` accepts:

```text
--config PATH              required YAML config
--gpu IDS                  defaults to 0; ignored when CUDA_VISIBLE_DEVICES is already set
--train | --validate | --test | --export   exactly one mode is required
--gradio                   enables Gradio logging/progress assets
--verbose                  debug logging
--typecheck                jaxtyping/typeguard import hook for threestudio
```

Everything after known CLI flags is parsed by OmegaConf as config overrides, for example:

```bash
system.prompt_processor.prompt="a ceramic lion" data.image_path="load/images/lion_rgba.png"
```

If `CUDA_VISIBLE_DEVICES` is already set, `launch.py` uses all visible devices and ignores `--gpu` for filtering.

## Four-stage command chain

Set common variables:

```bash
prompt="a brightly colored mushroom growing on a log"
image_path="load/images/mushroom_log_rgba.png"
gpu="0"
```

### Stage 1A: coarse NeRF

Purpose: initialize coarse shape and appearance with an implicit volume and NeRF volume renderer.

```bash
python launch.py --config configs/dreamcraft3d-coarse-nerf.yaml --train --gpu "$gpu" \
  system.prompt_processor.prompt="$prompt" data.image_path="$image_path"
```

Expected checkpoint:

```text
outputs/dreamcraft3d-coarse-nerf/<prompt-with-spaces-as-underscores>@LAST/ckpts/last.ckpt
```

### Stage 1B: coarse NeuS

Purpose: refine the coarse representation with implicit SDF / NeuS while using the prior stage checkpoint.

```bash
ckpt="outputs/dreamcraft3d-coarse-nerf/<prompt-tag>@LAST/ckpts/last.ckpt"
python launch.py --config configs/dreamcraft3d-coarse-neus.yaml --train --gpu "$gpu" \
  system.prompt_processor.prompt="$prompt" data.image_path="$image_path" system.weights="$ckpt"
```

### Stage 2: geometry refinement

Purpose: convert to DMTet geometry with `tetrahedra-sdf-grid` and CUDA nvdiff rasterization.

```bash
ckpt="outputs/dreamcraft3d-coarse-neus/<prompt-tag>@LAST/ckpts/last.ckpt"
python launch.py --config configs/dreamcraft3d-geometry.yaml --train --gpu "$gpu" \
  system.prompt_processor.prompt="$prompt" data.image_path="$image_path" system.geometry_convert_from="$ckpt"
```

### Stage 3: texture refinement

Purpose: fix geometry and optimize texture with Stable Diffusion BSD guidance.

```bash
ckpt="outputs/dreamcraft3d-geometry/<prompt-tag>@LAST/ckpts/last.ckpt"
python launch.py --config configs/dreamcraft3d-texture.yaml --train --gpu "$gpu" \
  system.prompt_processor.prompt="$prompt" data.image_path="$image_path" system.geometry_convert_from="$ckpt"
```

## Validation/test/export modes

Use the same `--config` and overrides, but replace `--train` with exactly one of:

- `--validate`: validation dataloader and validation images/videos.
- `--test`: test dataloader and turntable-like video outputs.
- `--export`: prediction/export path, usually with `resume=<checkpoint>` and `system.exporter_type=mesh-exporter`.

Do not run validation/test/export without a compatible checkpoint when the config expects one.

## Post-stage checks

After each successful stage, check:

- `ckpts/last.ckpt` exists.
- `configs/parsed.yaml` exists for reproducibility and export.
- `cmd.txt`, `tb_logs`, `csv_logs`, or other logging folders are present when training ran.
- `save/` contains validation images/videos after validation/test/predict paths.

Use the export/output sub-skill for detailed output inspection.
