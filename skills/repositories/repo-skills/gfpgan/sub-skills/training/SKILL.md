---
name: training
description: "Use GFPGAN training, FFHQ degradation datasets, BasicSR configs,
  landmark preprocessing, model internals, and checkpoint conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# GFPGAN Training and Data Workflows

Use this sub-skill when a user asks to train, fine-tune, configure, or debug GFPGAN model/data workflows rather than simply restore an image.

## Use This For

- Preparing FFHQ-style disk or LMDB data for `FFHQDegradationDataset`.
- Explaining `options/train_gfpgan_v1.yml` and `options/train_gfpgan_v1_simple.yml`-style config sections.
- Running the BasicSR-backed training launcher and understanding why full training is GPU/multi-GPU and data/checkpoint heavy.
- Using `GFPGANModel`, `GFPGANv1`, `GFPGANv1Clean`, `GFPGANBilinear`, `FacialComponentDiscriminator`, ArcFace identity loss, and StyleGAN2 generator components.
- Parsing FFHQ landmarks for component crops.
- Converting bilinear/original checkpoints to clean checkpoints.
- Debugging LMDB suffix errors, missing component paths, missing pretrained checkpoints, CUDA/extension issues, and config mismatch errors.

## Route Elsewhere

- Restoring images/folders, choosing inference version defaults, output layout, and `GFPGANer.enhance`: use `../inference/`.
- Package-wide dependency import checks: start with `../../references/installation.md` and `../../scripts/check_env.py`.
- Replicate/Cog deployment details: treat as deployment-specific and outside this training sub-skill.

## Quick Start

Before full training, validate imports and a config/data shape without starting a long run:

```bash
python sub-skills/training/scripts/check_env.py --json
```

Generate a component-landmark file from FFHQ metadata when using `crop_components: true`:

```bash
python sub-skills/training/scripts/parse_ffhq_landmarks.py \
  --json-path ffhq-dataset-v2.json \
  --save-path FFHQ_eye_mouth_landmarks_512.pth \
  --scale 0.5 \
  --enlarge-ratio 1.4
```

Convert a bilinear/original GFPGAN checkpoint to a clean checkpoint when following the v1.2 fine-tuning path:

```bash
python sub-skills/training/scripts/convert_checkpoint_to_clean.py \
  --ori-path bilinear_or_original_checkpoint.pth \
  --save-path GFPGAN_clean_converted.pth \
  --narrow 1 \
  --channel-multiplier 2
```

## References

- `references/workflows.md`: training, fine-tuning, validation, landmark, and conversion workflows.
- `references/configuration.md`: YAML sections, network/loss/path/data settings, and config decision points.
- `references/data-layout.md`: disk/LMDB layout, landmark `.pth` schema, dataset outputs, and fixture checks.
- `references/model-architecture.md`: verified model/component signatures and behavior.
- `references/troubleshooting.md`: training-specific data, checkpoint, CUDA, OpenCV, and config failures.

## Bundled Scripts

- `scripts/check_env.py`: verifies training imports, key signatures, CUDA visibility, and optional dataset config readability.
- `scripts/parse_ffhq_landmarks.py`: parameterized FFHQ landmark parser adapted from the source script without hardcoded paths.
- `scripts/convert_checkpoint_to_clean.py`: parameterized checkpoint converter adapted from the source conversion script.

## Decision Notes

- Use the simple config when the user wants to avoid component landmarks; use the full config when component discriminators and identity loss are required.
- If `crop_components: true`, the training config must point to a compatible landmark `.pth` file.
- Treat full training as expensive. Prefer smoke tests and config validation unless the user explicitly wants a long GPU training run.
