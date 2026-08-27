---
name: data-preparation
description: "Prepare, inspect, and troubleshoot MMOCR dataset conversion and
  data layouts for text detection, recognition, spotting, and KIE."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMOCR Data Preparation

Use this sub-skill when the task is about OCR dataset preparation rather than
model training, inference, or low-level data-sample internals. It covers MMOCR
annotation schemas, dataset-zoo metadata, task-specific conversion choices,
recognition LMDB handling, generated dataset configs, and safe preflight checks.

## Start here

1. Read [data formats and datasets](references/data-formats-and-datasets.md)
   to choose between `textdet`, `textrecog`, `textspotting`, and `kie` and to
   verify the annotation shape expected by MMOCR.
2. Run the bundled no-download preflight before any conversion or training:

   ```bash
   python scripts/mmocr_dataset_preflight.py --list
   python scripts/mmocr_dataset_preflight.py --dataset icdar2015 --task textdet
   ```

   Pass `--dataset-zoo-path <dataset_zoo>` when checking a project-local or
   private dataset-zoo directory.
3. Read [data preparation workflows](references/data-preparation-workflows.md)
   before planning official dataset preparation, private dataset-zoo entries,
   LMDB recognition data, generated config placement, or visualization.
4. Read [troubleshooting](references/troubleshooting.md) when a dataset/task is
   unsupported, a converter wants network access, split selection is wrong,
   configs are not overwritten, images/annotations do not resolve, LMDB loading
   fails, text encodings are broken, KIE labels are inconsistent, or a dataset
   browser has no display.

## Route here for

- Choosing `--task textdet`, `textrecog`, `textspotting`, or `kie` for a public
  or private OCR dataset.
- Inspecting dataset-zoo names, task coverage, license metadata, split support,
  and generated config names.
- Preparing MMOCR JSON annotations with `data_list`, `img_path`, `bbox`,
  `polygon`, `text`, `ignore`, and `metainfo` fields.
- Planning recognition crops, dictionaries, and optional LMDB output.
- Debugging `data_root`, `data_prefix`, `ann_file`, and pipeline loader
  interactions before training/evaluation.
- Treating dataset visualization as an optional, reference-only sanity check.

## Route elsewhere

- Training/evaluation command construction, config inheritance, runner flags,
  metrics, checkpoints, and distributed launch: use
  [training-evaluation-configs](../training-evaluation-configs/SKILL.md).
- Inferencer calls, prediction outputs, visualization outputs from inference,
  and OCR pipeline inference: use [ocr-inference](../ocr-inference/SKILL.md).
- DataSample class internals, registries, model components, transforms beyond
  loader compatibility, dictionaries as model components, and custom component
  extension: use [model-api-components](../model-api-components/SKILL.md).

## Source-script policy

- The bundled `scripts/mmocr_dataset_preflight.py` is the safe default. It only
  reads metadata or tiny annotations and never downloads datasets.
- The official unified dataset preparer can download, extract, move, delete, and
  write configs. Use its CLI semantics only after the user approves data,
  network, storage, and overwrite behavior.
- Dataset-specific converters and dataset browsing utilities are reference-only
  for this sub-skill: distill their behavior into a plan, keep sample counts
  tiny, and do not depend on GUI or large downloads for validation.
