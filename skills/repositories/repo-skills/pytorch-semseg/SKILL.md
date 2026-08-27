---
name: pytorch-semseg
description: "Use pytorch-semseg for PyTorch semantic segmentation model
  selection, config/data preparation, training and validation planning,
  single-image inference, and legacy compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pytorch-semseg

Use this repo skill when a task involves the `ptsemseg` package or the historical pytorch-semseg semantic-segmentation workflows: FCN, U-Net, SegNet, PSPNet, ICNet, LinkNet, FRRN, dataset YAML configs, training/validation entry points, single-image mask inference, or legacy dependency errors.

## Before acting

1. Confirm the user is working with pytorch-semseg or an equivalent checkout/package that exposes `ptsemseg`.
2. Read [references/repo-provenance.md](references/repo-provenance.md) when deciding whether this skill matches the current repository snapshot or should be refreshed.
3. Read [references/compatibility.md](references/compatibility.md) before installing dependencies, adapting old scripts, or promising exact legacy reproduction.
4. Run the bundled environment check when imports or backend support matter:

   ```bash
   python scripts/check_environment.py
   python scripts/check_environment.py --smoke
   ```

The environment check is safe by default: it imports packages, reports torch/CUDA visibility, flags protobuf/SciPy/DenseCRF hazards, and optionally runs a tiny no-download FRRN CPU smoke.

## Route map

| User task | Read this |
| --- | --- |
| Choose a model id, instantiate a model, inspect losses/optimizers/schedulers/augmentations/metrics, or debug registry/API failures. | [sub-skills/model-zoo-and-apis/SKILL.md](sub-skills/model-zoo-and-apis/SKILL.md) |
| Write or validate a YAML config, choose dataset loader keys/splits, check data layout, or explain config drift. | [sub-skills/data-and-configs/SKILL.md](sub-skills/data-and-configs/SKILL.md) |
| Plan training or validation commands, reason about checkpoints/logs/metrics, or avoid expensive data-bound runs. | [sub-skills/training-and-evaluation/SKILL.md](sub-skills/training-and-evaluation/SKILL.md) |
| Build or debug one-image segmentation inference commands, output mask writing, checkpoint filename parsing, or DenseCRF. | [sub-skills/single-image-inference/SKILL.md](sub-skills/single-image-inference/SKILL.md) |
| Diagnose install/import/backend issues that cut across workflows. | [references/troubleshooting.md](references/troubleshooting.md) and [references/compatibility.md](references/compatibility.md) |

## Install and import baseline

This snapshot exposes `ptsemseg` but may not behave like a modern packaged project. A future agent should first make `ptsemseg` importable from the user's selected package or checkout, then verify:

```bash
python - <<'PY'
from ptsemseg.models import get_model
from ptsemseg.loader import get_loader
print(get_model)
print(get_loader('pascal'))
PY
```

If importing `ptsemseg.models` fails with a generated protobuf descriptor error, read [references/compatibility.md](references/compatibility.md) before changing package versions. If `tensorboardX`, `pydensecrf`, or legacy SciPy image helpers are missing, route to the workflow-specific troubleshooting reference instead of installing broad extras blindly.

## Key capabilities

- Model registry guidance for `fcn32s`, `fcn16s`, `fcn8s`, `unet`, `segnet`, `pspnet`, `icnet`, `icnetBN`, `linknet`, `frrnA`, and `frrnB`.
- Dataset/config guidance for `pascal`, `camvid`, `ade20k`, `mit_sceneparsing_benchmark`, `cityscapes`, `nyuv2`, `sunrgbd`, and `vistas`.
- Static YAML validation that avoids dataset reads and catches unsupported keys, machine-specific paths, legacy `l_rate`/`l_schedule`, unsafe `img_rows/img_cols: same`, Pascal SBD pitfalls, and registry typos.
- Dry-run command builders for training, validation, and single-image inference. These helpers print commands and warnings; they do not run long training, validation, image inference, downloads, or destructive writes.
- Troubleshooting for protobuf/caffe metadata, PyYAML loader behavior, FCN/SegNet pretrained VGG side effects, DenseCRF optional dependency, SciPy image helper removal, checkpoint `module.` prefixes, and CPU/CUDA expectations.

## Safety and backend notes

- CPU checks are sufficient for import, parser, config, registry, metrics, and a small FRRN smoke. CUDA is optional for performance and realistic full-size training/inference; do not use a CPU import check as proof of GPU performance.
- Real training and validation require user-supplied datasets and may write logs/checkpoints. Use the dry-run builders and obtain explicit approval before running expensive commands.
- Real single-image inference requires a trained checkpoint and input image; optional DenseCRF requires `pydensecrf`.
- FCN and SegNet instantiation through `get_model` may request pretrained VGG weights. Use FRRN or other no-download checks for routine smoke tests unless weight downloads/cache access are allowed.

## Bundled files

- [references/repo-provenance.md](references/repo-provenance.md) — source snapshot and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) — structured router metadata for managed imports.
- [references/compatibility.md](references/compatibility.md) — dependency, protobuf, SciPy, CUDA, and packaging constraints.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting failure triage.
- [scripts/check_environment.py](scripts/check_environment.py) — safe import/backend/API smoke helper.
