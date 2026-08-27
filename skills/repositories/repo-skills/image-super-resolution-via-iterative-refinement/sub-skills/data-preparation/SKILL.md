---
name: data-preparation
description: "Prepare and validate LR/HR/SR dataset layouts for image-directory
  and LMDB workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-preparation

Use this sub-skill for dataset roots, resize layouts, and safe fixture checks.

## Route here when
- A user asks how to prepare SR triplets for `datatype: img` or `datatype: lmdb`.
- A config uses `dataroot`, `l_resolution`, `r_resolution`, `datatype`, `mode`, or `data_len`.
- A dataset root is missing `lr_<L>`, `hr_<R>`, or `sr_<L>_<R>`.
- An LMDB root fails to load because keys or `length` are missing.
- You need a deterministic tiny dataset for smoke testing.

## Start with
1. [references/data-layouts.md](references/data-layouts.md) for the directory and LMDB contracts.
2. [scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py) to check an existing `img` root.
3. [scripts/prepare_tiny_dataset.py](scripts/prepare_tiny_dataset.py) to create a small RGB fixture.

## What this sub-skill covers
- LR/HR/SR triplet directory layout.
- LMDB key layout and length metadata.
- Dataset config fields that control loading.
- Common data-shape, naming, and mode mismatches.

## What it does not cover
- Training, validation, inference, or metric workflows.
- Network downloads or large-scale preprocessing jobs.
- Model architecture or checkpoint selection.

## Usage notes
- `mode: LRHR` expects LR, HR, and SR data.
- `mode: HR` reads HR and SR only, but the preparation layout still includes all triplets.
- Keep directory contents image-only and aligned by relative path.
- The bundled validator is for `img` layouts; LMDB checks are described in the references.

## Bundled files
- [references/data-layouts.md](references/data-layouts.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py)
- [scripts/prepare_tiny_dataset.py](scripts/prepare_tiny_dataset.py)
