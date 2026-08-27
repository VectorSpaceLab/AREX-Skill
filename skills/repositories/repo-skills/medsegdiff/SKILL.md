---
name: medsegdiff
description: "Guide MedSegDiff medical-image segmentation workflows for dataset
  preparation, diffusion-model training, checkpoint sampling, ensemble
  aggregation, and evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MedSegDiff

MedSegDiff is a repository-level PyTorch diffusion framework for medical-image
segmentation. Use this skill when a task mentions MedSegDiff, its ISIC or BRATS
examples, diffusion-based segmentation, the `guided_diffusion` modules, or the
repository's segmentation train/sample/evaluation workflows.

## First route

- **Prepare or validate data**: read
  [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).
  It covers ISIC CSV/image/mask trees, BRATS NIfTI modalities and slices, and
  custom 2D/3D layouts.
- **Configure or plan training**: read
  [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md). It covers the
  training CLI contract, model/diffusion factories, schedules, checkpoints,
  mixed precision, and multi-GPU behavior.
- **Sample or score predictions**: read
  [`sub-skills/inference-evaluation/SKILL.md`](sub-skills/inference-evaluation/SKILL.md).
  It covers checkpoint compatibility, DDIM/DPM-Solver options, ensembles,
  STAPLE aggregation, output naming, IoU/Dice, and per-class metrics.

For a task spanning multiple routes, prepare and validate the data first, then
train or provide a compatible checkpoint, then sample and evaluate. Preserve
the dataset branch, effective input channels, image size, model `version`,
diffusion schedule, and checkpoint settings across every stage.

## Installation and runtime gate

The upstream repository has no `pyproject.toml`, `setup.py`, console entry
point, or formal package metadata. Its documented dependency source is
`requirement.txt`. In a fresh isolated environment, install the public runtime
dependencies and make the checkout importable before using its Python modules:

```bash
python -m pip install -r requirement.txt
PYTHONDONTWRITEBYTECODE=1 python -c "import guided_diffusion.script_util as s; print(s.model_and_diffusion_defaults())"
```

Use a CUDA-enabled PyTorch build for actual training or sampling. CPU checks are
appropriate for data loaders, metric helpers, and small factory/API smokes,
but CPU is not a truthful substitute for the full training/sampling path: the
runtime uses CUDA device placement and, during sampling, CUDA timing events and
synchronization.

Before a real run, use the bundled safe inspectors and environment reference:

- [`scripts/check_environment.py`](scripts/check_environment.py) checks Python,
  imports, and optional CUDA availability without downloading data or starting
  training.
- [`references/api-reference.md`](references/api-reference.md) records the
  verified module and factory contracts.
- [`references/troubleshooting.md`](references/troubleshooting.md) handles
  cross-cutting install, import, backend, checkpoint, and path failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) tells you
  when the source baseline is stale and a refresh is warranted.

Keep medical data, checkpoints, predictions, and generated results outside the
skill directory. Do not assume the repository's example data is complete; use
the data-preparation validator and fetch data only through an approved,
user-controlled source.

## Shared invariants

- The model factory's default `image_size` is 64, while the documented example
  recipes commonly use 256; only 64, 128, 256, and 512 have automatic channel
  multipliers in the inspected source.
- Boolean options use an explicit value such as `True` or `False`, not a bare
  `store_true` switch.
- `data_name=ISIC` and `data_name=BRATS` select dedicated branches; other values
  select the custom branch, whose 2D/3D detection has source-specific behavior.
- Keep `batch_size=1` for the unpatched sampler because several output-ID paths
  use the first item of a batch.
- Treat `version`, effective input channels, architecture flags, diffusion
  steps/schedule, and checkpoint state as one compatibility tuple.

This skill is guidance for operating the public repository; it does not claim
medical validity, reproduce paper metrics without the required data/checkpoint,
or replace clinical review.
