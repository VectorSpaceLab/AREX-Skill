---
name: "single-model-inference"
description: "Use for PaddleCV config-driven single-model classification,
  detection, segmentation, feature extraction, and keypoint inference
  workflows."
metadata:
  disco-role: "operating"
disable-model-invocation: true
license: Apache 2.0
---

# Single-model inference

Use this sub-skill when the user wants one PaddleCV model family at a time: classification, detection, segmentation, feature extraction, or keypoint estimation.

## Covers
- `paddlecv/configs/single_op/*.yml`
- `Pipeline(config_path=...)` for a single model graph
- `tools/predict.py` style inference for one image, a directory of images, or a video
- model catalog discovery that helps choose a single-op preset

## Excludes
- `PaddleCV(task_name=...)` system presets such as OCR, PP-Structure, ShiTu, Human, Vehicle, TinyPose, IE, SA, and TTS
- custom operator registration and DAG validation
- connector/output authoring beyond the built-in single-op outputs

## Read these files
- `../../references/task-catalog.md` for the single-op preset list and config families.
- `../../references/api-reference.md` for `PaddleCV`, `Pipeline`, and config parsing details.
- `../../references/workflows.md` for the canonical command patterns.
- `../../references/troubleshooting.md` for import, cache, and config errors.
- `../../scripts/run_predict.py` for the bundled public inference wrapper.

## Typical user requests
- "Run PP-YOLOE+ on one image"
- "Use the single-op config for PP-HGNet"
- "List the supported single-op models"
- "Why does the detection config fail to resolve an input key?"

## Core workflow
1. Pick a `paddlecv/configs/single_op/*.yml` file or a matching direct config path.
2. Run `scripts/run_predict.py --config ... --input ...`.
3. Override the YAML with `-o KEY=VALUE` only when the config needs a small local adjustment.
4. Use `PaddleCV.list_all_supported_models()` or `list_model([...])` to narrow model choice.

## Model families
- Classification: `PP-LCNet`, `PP-LCNetV2`, `PP-HGNet`
- Detection: `PP-YOLO`, `PP-YOLOv2`, `PP-YOLOE`, `PP-YOLOE+`, `PP-PicoDet`
- Segmentation: `PP-HumanSegV2`, `PP-LiteSeg`, `PP-MattingV1`
- Feature extraction: use embedding-style single-op configs such as `paddlecv/configs/unittest/test_feature_extraction.yml`.
- Keypoint: use pose-estimation single-op configs such as `paddlecv/configs/unittest/test_keypoint.yml`.

## Output shapes to expect
- Classification: class ids, scores, and label names.
- Detection: bounding boxes, scores, class ids, and class names.
- Segmentation: segmentation masks or alpha outputs.
- Feature extraction: bounding boxes plus features and retrieval metadata.
- Keypoint: keypoints plus keypoint scores.

## Common failure modes
- `device` or `run_mode` is invalid.
- An `Inputs` entry points to the wrong prior op output.
- The input is not an image, directory, video, or supported in-memory array.
- Model/download resolution fails because the cache entry is missing or the network is unavailable.

## When to hand off
If the request shifts to OCR, PP-Structure, retrieval systems, or any bundled task preset, switch to `system-pipelines`. If the user wants to create or modify operators, switch to `custom-ops`.
