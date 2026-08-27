---
name: data-preparation
description: "Prepares and validates BDD100K-style YOLOP data roots, detection
  JSONs, drivable-area masks, lane-line masks, and label-generation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# YOLOP Data Preparation

Use this sub-skill when the task asks how to prepare BDD100K data for YOLOP, set `DATASET.*ROOT` config fields, diagnose missing masks/JSONs/images, generate drivable-area segmentation masks, or understand the detection label conversion used by `BddDataset`.

Do not use this sub-skill for model hyperparameters, checkpoint loading, ONNX export, or demo inference except where those tasks depend on data roots; route those to `training`, `export`, or `inference`.

## Read first

- [references/data-layout.md](references/data-layout.md) explains the expected BDD100K directory layout, how `BddDataset` maps mask paths to image/label/lane paths, and how detection categories are converted.
- [references/troubleshooting.md](references/troubleshooting.md) covers empty datasets, missing path pairs, malformed JSONs, mask rendering failures, and common config mistakes.
- Run [scripts/check_data_layout.py](scripts/check_data_layout.py) before training/evaluation to check that roots and split directories line up.
- Run [scripts/generate_drivable_masks.py](scripts/generate_drivable_masks.py) when you need a safer, argument-driven version of the repo's drivable-area mask generator.

## Minimal workflow

1. Acquire the BDD100K images and the YOLOP-compatible detection, drivable-area, and lane-line annotations from the source project instructions or an already prepared mirror.
2. Put the roots into one of these forms:
   - README combined layout: `images/{train,val}`, `det_annotations/{train,val}`, `da_seg_annotations/{train,val}`, `ll_seg_annotations/{train,val}` under one dataset root.
   - Source config layout: independent roots where each root contains `train/` and `val/` subdirectories.
3. If drivable masks are not already PNG files, generate them from BDD polygon JSONs with the bundled generator.
4. Validate the roots and filename correspondence.
5. Update `cfg.DATASET.DATAROOT`, `LABELROOT`, `MASKROOT`, and `LANEROOT` before running training or evaluation.

## Safe helpers

```bash
# Combined README-style root
python sub-skills/data-preparation/scripts/check_data_layout.py \
  --dataset-root /path/to/yolop-dataset --splits train val --max-samples 20

# Explicit roots matching lib/config/default.py fields
python sub-skills/data-preparation/scripts/check_data_layout.py \
  --images-root /path/to/images/100k \
  --det-root /path/to/det_annotations \
  --da-root /path/to/da_seg_annotations \
  --lane-root /path/to/ll_seg_annotations

# Generate drivable-area masks for one split from BDD label JSONs
python sub-skills/data-preparation/scripts/generate_drivable_masks.py \
  --labels-dir /path/to/bdd100k/labels/100k/train \
  --output-dir /path/to/bdd_seg_gt/train
```

These helpers do not import YOLOP source code. They validate/generate files from paths you pass explicitly and are safe to run outside the original repo checkout.

## Key ownership boundary

This sub-skill owns data layout and label generation. Once the layout is valid, use [../training/SKILL.md](../training/SKILL.md) for `tools/train.py` and `tools/test.py` config choices, metrics, and checkpoint behavior.
