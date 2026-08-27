---
name: prediction-and-inference
description: "Routes EasyCV predictor APIs, batch prediction, feature
  extraction, and exported-model inference."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Prediction and inference

Use this sub-skill when the task is to run EasyCV inference from Python, a batch file or ODPS table, or an exported raw / JIT / Blade / ONNX-style model.

It covers the predictor family under `easycv.predictors` and the batch front door `python -m easycv.tools.predict`.

## Read these references first

- `references/predictors.md` for the major predictor classes and their shared constructor patterns.
- `references/batch-prediction.md` for file-list and table-based batch inference.
- `references/troubleshooting.md` for missing extras, model-type mismatches, and shape / label issues.
- Root `references/cli-reference.md` for the installed-package command front doors.

## What belongs here

Include tasks such as:

- running classification, detection, segmentation, pose, OCR, video, ReID, feature-extraction, or BEVFormer inference
- selecting the right predictor class for the exported artifact you already have
- loading raw, JIT, Blade, or ONNX-style model files
- batch prediction over local files, URLs, or ODPS tables
- label-map handling, score thresholds, and `topk` output shaping
- image-mode issues such as `BGR` vs `RGB`

## What stays elsewhere

- Training / validation / config selection -> `sub-skills/training-and-evaluation/`
- Export and optimization of the model artifact -> `sub-skills/export-and-optimization/`
- Dataset conversion, file layouts, and OSS setup -> `sub-skills/data-preparation/`

## Typical decision flow

1. Decide whether you want a direct predictor or the batch tool.
2. Identify the model family and the artifact format.
3. Check whether you have a config file, label map, or exported sidecar files.
4. Confirm the input form: file path, image array, list file, or ODPS table.
5. Run the smallest safe inference path first, then scale to batches or tables.

## Common success signals

- The predictor class matches the model artifact type.
- The input processor accepts the image mode and file format.
- The output processor returns the expected `class`, `detection_boxes`, `keypoints`, `feature`, or similar fields.
- Batch inference writes the expected output file or table columns.

## Common prediction surfaces

- `easy_predict` is required for the batch-file / table CLI.
- Exported JIT / Blade models usually need their sidecar config or preprocess artifact nearby.
- `mode='RGB'` is common for PIL-based classification; many detection pipelines remain `BGR`.
- `label_map_path` or `CLASSES` controls readable class names.

