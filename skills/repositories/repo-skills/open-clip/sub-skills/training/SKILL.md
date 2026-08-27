---
name: training
description: "Construct and debug OpenCLIP task-era and legacy training
  commands, data loaders, task/loss wrappers, compile, FSDP, precision,
  optimizer, scheduler, and checkpoint options."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training

Use this sub-skill when an agent needs to build or troubleshoot OpenCLIP training commands, data layouts, task/loss wrappers, optimizer/scheduler settings, precision, `torch.compile`, distributed/FSDP, or checkpoint/resume behavior.

## Route Here

- Launch training with `python -m open_clip_train.main` or legacy compatibility training with `python -m open_clip_train.legacy_main`.
- Choose `--dataset-type` among `csv`, `webdataset`, `synthetic`, `webdataset-audio`, `synthetic-audio`, or `auto`.
- Explain dict batch contracts such as `{"image": ..., "text": ...}`, `{"audio": ..., "text": ...}`, nested NaFlex patch/audio dicts, and optional `text_valid` masks.
- Select `CLIPTask`, `SigLIPTask`, `CoCaTask`, `DistillCLIPTask`, `CLAPTask`, `GenLipTask`, or `GenLapTask` behavior via model and CLI flags.
- Tune optimizer, scheduler, precision, gradient accumulation, loss options, `torch.compile`, FSDP2, full/sharded checkpoints, resume/latest, and remote sync.
- Run safe parser and CSV data smoke checks without training.

## Read First

- `references/cli-reference.md` for command construction, default parser facts, and option families.
- `references/data-formats.md` for CSV, WebDataset, synthetic, audio, dict batch, and validation contracts.
- `references/task-api.md` for `TrainingTask` wrappers, loss creation, batch preparation, and dummy batches.
- `references/checkpoints-distributed.md` for resume, checkpoint, FSDP, compile, precision, optimizer, and scheduler decisions.
- `references/troubleshooting.md` for common failures and fixes.

## Safe Helpers

- `scripts/training_arg_report.py` imports `open_clip_train.params.parse_args`, parses OpenCLIP training args, and prints selected defaults/options without constructing models, data loaders, or training.
- `scripts/validate_csv_dataset.py` validates CSV/TSV image path and caption columns, optional separators/keys, numeric-caption stringification, and image path existence without loading OpenCLIP or starting training.

## Quick Starts

Inspect parser defaults and a planned command:

```bash
python sub-skills/training/scripts/training_arg_report.py -- --dataset-type csv --train-data DATA/train.tsv --model ViT-B-32
```

Validate a TSV dataset before training:

```bash
python sub-skills/training/scripts/validate_csv_dataset.py DATA/train.tsv --image-key filepath --caption-key title --separator tab
```

Minimal CPU-safe synthetic smoke command shape:

```bash
python -m open_clip_train.main --dataset-type synthetic --train-num-samples 16 --batch-size 4 --epochs 1 --workers 0 --device cpu --model RN50
```

## Boundaries

- Pure model loading, tokenization, preprocessing, embeddings, and inference route to `../model-inference/SKILL.md`.
- CLAP audio model setup, audio zero-shot evaluation, and audio-specific data details route to `../audio-clap/SKILL.md`.
- NaFlex token-budget tuning, patch dictionary details, GenLIP/GenLAP generation behavior, and NaFlex scripts route to `../naflex-generative/SKILL.md`.
- Evaluation metrics, zero-shot/retrieval reporting, checkpoint conversion, export, and Hugging Face publishing route to `../evaluation-conversion/SKILL.md`.
