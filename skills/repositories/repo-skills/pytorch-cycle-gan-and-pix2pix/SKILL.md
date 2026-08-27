---
name: pytorch-cycle-gan-and-pix2pix
description: "Guide CycleGAN and pix2pix image-to-image translation,
  colorization, dataset preparation, checkpoint inference, and custom model or
  dataset extensions in this PyTorch repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# pytorch-CycleGAN-and-pix2pix

Use this repo skill when a task involves the PyTorch CycleGAN/pix2pix repository, paired or unpaired image-to-image translation, colorization, `train.py`/`test.py`, dataset modes such as `aligned` or `unaligned`, pretrained generator checkpoints, or custom model/dataset templates.

## Install and inspect first

This is a checkout-oriented project, not a pip distribution. Use the documented Python 3.11/PyTorch 2.4 baseline in [`references/installation.md`](references/installation.md), then run the bundled environment check against the target checkout:

```bash
python scripts/check_env.py --repo-root TARGET_CHECKOUT
```

The required verified scope is CPU-compatible. CUDA/DDP, Caffe Cityscapes evaluation, and HED edge extraction are optional external surfaces; do not treat a CPU import as GPU verification.

Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill matches the current repository state. Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting dependency, path, backend, and source caveats.

## Route by task

- **Train/test/apply models, resume training, checkpoints, W&B/HTML, CPU/GPU/DDP:** read [`sub-skills/translation-workflows/SKILL.md`](sub-skills/translation-workflows/SKILL.md).
- **Prepare/download/validate data, combine A/B pairs, convert Cityscapes:** read [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).
- **Add a custom model or dataset, edit templates, debug registry naming or option injection:** read [`sub-skills/customization/SKILL.md`](sub-skills/customization/SKILL.md).

## Core decision points

1. Choose the data mode before writing a command: CycleGAN uses `unaligned`, pix2pix uses `aligned`, one-sided generator application uses `single`, and colorization uses `colorization`.
2. Validate the data root with the data-preparation helper before a real train/test run.
3. Keep model architecture, normalization, channel counts, direction, and dropout/checkpoint suffixes aligned between training and testing.
4. The current parser has no `--gpu_ids` option: it auto-selects CPU when CUDA is unavailable and `cuda:0` otherwise. Use a CPU-only PyTorch environment or prefix a Linux command with `CUDA_VISIBLE_DEVICES=` to hide GPUs. Use `torchrun` only after a bounded DDP setup smoke; the current source has a synchronized-normalization naming/guard inconsistency.
5. Treat network downloads, external Caffe/MATLAB workflows, and long training as explicit user-approved operations, not automatic verification steps.

## Shared helper

[`scripts/check_env.py`](scripts/check_env.py) checks dependency imports, optional CUDA availability, repo module imports, and a tiny CPU generator smoke. It does not download assets, load checkpoints, train, or write result files.

For a self-contained command builder, use [`sub-skills/translation-workflows/scripts/build_command.py`](sub-skills/translation-workflows/scripts/build_command.py). For safe data preparation, use the scripts linked from [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).
