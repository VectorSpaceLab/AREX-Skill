---
name: segmentation
description: "Guides Attention-Gated Networks medical image segmentation
  workflows, including 3D U-Net training, validation, NIfTI layouts, and
  attention or feature-map export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Segmentation

Use this sub-skill for medical image segmentation tasks in Attention-Gated
Networks. It covers 2D/3D U-Net variants, CT deep-supervision networks,
attention-gated U-Nets, non-local blocks, NIfTI datasets, segmentation
training/validation scripts, and feature or attention map exports.

## Read first

- Read [api-reference.md](references/api-reference.md) when you need exact
  model names, wrapper methods, dataset class signatures, metric functions, or
  hookable layer names.
- Read [data-layout.md](references/data-layout.md) before arranging NIfTI data
  or debugging split, image/label, and transform problems.
- Read [workflows.md](references/workflows.md) for training, validation,
  checkpoint use, and safe attention/feature map export.
- Read [troubleshooting.md](references/troubleshooting.md) for CUDA, memory,
  SimpleITK, torchsample, NIfTI, shape, metric, or layer-hook failures.
- Run [run_segmentation.py](scripts/run_segmentation.py) for skill-owned
  training commands that replace the source repo's root training entry point.
- Run [validate_and_export_maps.py](scripts/validate_and_export_maps.py) to
  replace hard-coded validation and feature-map scripts with a parameterized,
  skill-owned helper.
- For fast environment validation, run the root helper
  `../../scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode segmentation`.

## When to use this sub-skill

Use this route when the user asks to:

- train a segmentation network from the repository configs;
- choose between baseline U-Net, non-local U-Net, CT deep supervision, and
  multi-attention U-Net variants;
- validate a segmentation checkpoint and compute dice, IoU, precision/recall,
  mean distance, or Hausdorff-style distances;
- arrange 3D NIfTI data for `acdc_sax`, `ukbb_sax`, `rvsc_sax`, or `test_sax`;
- export NIfTI predictions, attention volumes, feature maps, or slice previews;
- debug 3D shape, memory, CUDA, SimpleITK, torchsample, or layer-hook issues.

Route ultrasound scan-plane classification and 2D attention overlays to
`../classification/SKILL.md` instead.

## Quick workflow

1. Install the repository with CUDA-enabled PyTorch, torchsample, NIfTI, and
   visualization dependencies. Then run:

   ```bash
   python ../../scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode segmentation
   ```

2. Arrange NIfTI files under split directories with paired `image/` and
   `label/` subfolders. See [data-layout.md](references/data-layout.md).
3. Copy a CT config and replace `data_path.acdc_sax` with the current dataset
   root. The stock configs use `output_nc=4`, `tensor_dim='3D'`, and
   `gpu_ids=[0]`.

Relative config paths are resolved from the explicit `--repo-root`; relative
`data_path` values are resolved from the config file's parent. NIfTI data and
model weights/checkpoints must exist externally. The bundled runner and
`check_env.py --config ...` fail fast on missing or private `/vol/...` paths;
they never fabricate data.
4. Train with the bundled replacement:

   ```bash
   python scripts/run_segmentation.py --repo-root /path/to/Attention-Gated-Networks --config path/to/config.json
   ```

5. Validate a checkpoint or export maps with the bundled helper:

   ```bash
   python scripts/validate_and_export_maps.py --repo-root /path/to/Attention-Gated-Networks --config path/to/config.json --checkpoint path/to/checkpoint.pth --output-dir /tmp/ag-net-validation --mode validate
   ```

6. For safe smoke validation or map export without private paths, use:

   ```bash
   python scripts/validate_and_export_maps.py \
     --repo-root /path/to/Attention-Gated-Networks \
     --config configs/config_unet_ct_multi_att_dsv.json \
     --output-dir /tmp/ag-net-segmentation \
     --mode both
   ```

## Key decisions

- CUDA is required for the unmodified source wrappers. A CPU-only install does
  not verify the selected segmentation workflows.
- `unet_ct_dsv` is the simpler CT deep-supervision route; use
  `unet_ct_multi_att_dsv` when attention maps are a first-class goal.
- Real CT configs use large volumes (`160 x 160 x 96` patches). The generated
  helper's `16 x 16 x 16` synthetic volume is only a wiring smoke.
- The source validation and map-export scripts hard-code private paths. Prefer
  the bundled helper or explicitly parameterize a project-local copy.
- The source CRF post-processing script is reference-only, not bundled as a
  safe helper.

## Expected outputs

Training writes checkpoints and logs below the configured checkpoint directory
and experiment name. Validation writes NIfTI predictions and CSV metrics. The
bundled helper writes synthetic or fixture NIfTI outputs, `metrics.json`,
feature/attention-map NIfTI files, and middle-slice preview PNGs to the selected
output directory.
