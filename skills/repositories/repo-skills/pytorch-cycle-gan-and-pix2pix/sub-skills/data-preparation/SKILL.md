---
name: data-preparation
description: "Plan, validate, and convert datasets for CycleGAN, pix2pix,
  single-image, colorization, and Cityscapes workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data preparation

Use this sub-skill when the task is to acquire or plan datasets, validate standard dataset layouts, combine paired A/B folders into side-by-side pix2pix images, convert Cityscapes-style files, or understand optional edge/evaluation data workflows for this repository.

Route elsewhere when the request is really about:

- training, testing, pretrained inference, CPU/GPU/DDP command construction, checkpoints, W&B, or results HTML: [`translation-workflows`](../translation-workflows/SKILL.md)
- implementing or debugging custom model/dataset classes, registry naming, parser injection, or data dictionaries: [`customization`](../customization/SKILL.md)
- running external Caffe/MATLAB Cityscapes metrics or HED edge extraction as a required backend gate: keep them reference-only unless the user explicitly provides those external prerequisites.

## References and helpers

- [`references/data-layouts.md`](references/data-layouts.md): dataset modes, required folders, supported image extensions, phases, A/B orientation, and model compatibility.
- [`references/asset-downloads.md`](references/asset-downloads.md): dataset names accepted by the download helpers, URL patterns, Cityscapes license exception, and network/storage warnings.
- [`references/advanced-external-workflows.md`](references/advanced-external-workflows.md): optional Cityscapes FCN evaluation and HED edge extraction interfaces, prerequisites, and exclusion rationale.
- [`references/troubleshooting.md`](references/troubleshooting.md): empty/missing folders, filename and size mismatches, crop/load-size issues, download failures, Cityscapes conversion errors, and historical combiner caveats.
- [`scripts/validate_layout.py`](scripts/validate_layout.py): safe import-free dataset layout validator for `--mode unaligned|aligned|single|colorization --dataroot DATASET_ROOT`.
- [`scripts/combine_pairs.py`](scripts/combine_pairs.py): Pillow-based A/B folder combiner for explicit fold paths or `trainA/trainB/testA/testB` dataset roots.
- [`scripts/prepare_cityscapes_dataset.py`](scripts/prepare_cityscapes_dataset.py): self-contained Cityscapes converter that writes both paired `train/test` and unpaired `trainA/trainB/testA/testB` layouts.

## Operating order

1. Identify the target workflow and dataset mode before moving files: CycleGAN uses `unaligned`, pix2pix uses `aligned`, one-sided generator inference uses `single`, and colorization uses `colorization`.
2. Check the expected folder layout in [`references/data-layouts.md`](references/data-layouts.md), then run [`scripts/validate_layout.py`](scripts/validate_layout.py) before any training/test command is attempted.
3. If public assets are requested, consult [`references/asset-downloads.md`](references/asset-downloads.md); do not perform network downloads unless the user explicitly approves the dataset name, license obligations, storage location, and expected size.
4. For paired pix2pix data that currently exists as separate A and B images, combine with [`scripts/combine_pairs.py`](scripts/combine_pairs.py). Keep strict filename and size matching unless the user deliberately preprocesses images first.
5. For Cityscapes, require already downloaded and extracted `gtFine` and `leftImg8bit` trees, then convert with [`scripts/prepare_cityscapes_dataset.py`](scripts/prepare_cityscapes_dataset.py). Validate the paired and unpaired outputs afterward.
6. When the data root is valid and the user asks to train or test, hand off to [`translation-workflows`](../translation-workflows/SKILL.md) instead of continuing here.
