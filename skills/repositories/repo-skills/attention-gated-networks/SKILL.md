---
name: attention-gated-networks
description: "Guides Attention-Gated Networks PyTorch medical imaging workflows
  for ultrasound classification, attention-gated U-Net segmentation, data
  layout, CUDA setup, and visualization helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Attention-Gated Networks

Use this repo skill when a task involves the `Attention-Gated-Networks` PyTorch
repository or its medical imaging workflows: ultrasound scan-plane
classification, Sononet Grid Attention, Attention U-Net style segmentation,
NIfTI/HDF5 data layouts, CUDA setup, and attention or feature-map visualization.

## Start here

- Read [package-overview.md](references/package-overview.md) for package
  purpose, installation guidance, config families, generated helpers, and the
  CUDA policy.
- Read [troubleshooting.md](references/troubleshooting.md) for cross-cutting
  install/import, CUDA, Visdom, dependency, and config portability failures.
- Read [repo-provenance.md](references/repo-provenance.md) before deciding
  whether this skill is current for a checkout or before running a refresh.
- Use [repo-routing-metadata.json](references/repo-routing-metadata.json) only
  for router/import metadata.
- Run [check_env.py](scripts/check_env.py) after installation to verify imports,
  CUDA, and tiny model smokes.

## Route map

| User request | Read |
| --- | --- |
| Train, test, debug, or configure ultrasound scan-plane classification | [classification](sub-skills/classification/SKILL.md) |
| Use Sononet, Sononet2, Sononet Grid Attention, aggregated classifier, or attention overlays | [classification](sub-skills/classification/SKILL.md) |
| Arrange ultrasound HDF5 splits, labels, class weights, or samplers | [classification data layout](sub-skills/classification/references/data-layout.md) |
| Train, validate, or configure 2D/3D U-Net segmentation models | [segmentation](sub-skills/segmentation/SKILL.md) |
| Use CT deep supervision, multi-attention U-Net, non-local blocks, or NIfTI outputs | [segmentation](sub-skills/segmentation/SKILL.md) |
| Export 3D attention maps, feature maps, NIfTI predictions, or validation metrics | [segmentation workflows](sub-skills/segmentation/references/workflows.md) |
| Diagnose shared install, CUDA, dependency, or config issues | [troubleshooting](references/troubleshooting.md) |

## Minimal install check

After installing the repository and dependencies, run:

```bash
python scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode all
```

If the package is installed and importable without a checkout on `sys.path`, the
helper can still run from any working directory; `--repo-root` is only needed to
point at a local checkout during development or editable installs.

Successful output should include import success, CUDA availability, a tiny
classification output, an attention-classifier output, a tiny segmentation
output, and `check-env-ok`.

## Runtime and external inputs

The helpers require the repository checkout on `--repo-root` (or an installed
`AttentionGatedNetworks` package) plus the legacy runtime dependencies listed in
[package-overview.md](references/package-overview.md). Datasets and trained
weights/checkpoints are external inputs; this skill does not fabricate or
bundle them. Stock configs contain private historical `/vol/...` paths and must
be copied with `data_path.*` and output/checkpoint paths overridden.

For a config supplied as a relative path, always pass `--repo-root`; the helper
resolves the config from that root and any relative data path from the config's
parent, never from the process cwd. Validate before running:

```bash
python scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks \
  --config configs/config_sononet_grid_att_8.json --mode imports
```

This intentionally fails fast on private or missing data paths. The original
`train_classifaction.py` also contains a 10-hour final-epoch sleep; it is left
untouched as source evidence, while the bundled runner omits that hold.

## Important defaults

- Distribution: `AttentionGatedNetworks` version `1.0`.
- Import packages: `models`, `dataio`, `utils`.
- Required backend for the selected workflows: CUDA. The unmodified wrappers
  call `.cuda()` for models and tensors.
- Core dependencies: PyTorch, torchvision, torchsample, NumPy/SciPy,
  matplotlib, scikit-image, h5py, pandas, tqdm, Visdom, nibabel,
  scikit-learn, OpenCV, dominate, and SimpleITK for validation exports.
- Configs contain historical machine-specific dataset paths; copy the field
  structure but replace paths and output directories before use.
- Use the bundled scripts under this generated skill rather than hard-coded
  source visualization/validation scripts.

## Bundled helpers

- `scripts/check_env.py`: import, CUDA, classification, attention-classifier,
  and segmentation smoke checks.
- `sub-skills/classification/scripts/run_classifier.py`: training/testing
  replacement for classification workflows.
- `sub-skills/classification/scripts/export_attention_overlay.py`: safe
  attention overlay export for grid-attention classifiers.
- `sub-skills/segmentation/scripts/run_segmentation.py`: training replacement
  for segmentation workflows.
- `sub-skills/segmentation/scripts/validate_and_export_maps.py`: validation,
  NIfTI export, and feature/attention-map helper.

## Avoid when

Do not use this skill for unrelated modern MONAI/nnU-Net/TorchIO workflows
unless the task explicitly names Attention-Gated Networks or needs to port ideas
from this repository. Do not use it as proof that CPU-only execution works; the
selected repo workflows were verified as CUDA-required.
