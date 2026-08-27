---
name: "system-pipelines"
description: "Use for PaddleCV task-name and system-YAML pipelines such as OCR,
  PP-Structure, ShiTu, Human, Vehicle, TinyPose, IE, SA, and TTS."
metadata:
  disco-role: "operating"
disable-model-invocation: true
license: Apache 2.0
---

# System pipelines

Use this sub-skill for bundled multi-stage PaddleCV workflows: OCR, PP-Structure, ShiTu, Human, Vehicle, TinyPose, information extraction, sentiment analysis, and text-to-speech.

## Covers
- `PaddleCV(task_name=...)` routes for the packaged presets
- system YAMLs under `paddlecv/configs/system/`
- OCR, table, layout, retrieval, attribute, IE, SA, and TTS chains
- runtime download behavior, cache layout, and task-name selection

## Excludes
- single-op presets under `paddlecv/configs/single_op/`
- custom operator implementation details and registry plumbing
- pure training or tutorial reproduction material

## Read these files
- `../../references/task-catalog.md` for the packaged system presets and config families.
- `../../references/api-reference.md` for `PaddleCV` and `Pipeline` signatures.
- `../../references/workflows.md` for the common `task_name` and direct-config flows.
- `../../references/troubleshooting.md` for import, cache, and dependency issues.
- `../../scripts/run_predict.py` for the bundled runner that handles `--task-name`.

## Typical user requests
- "Run PP-OCRv3 on an image"
- "Use the built-in PP-Structure table pipeline"
- "Run sentiment analysis or TTS through PaddleCV"
- "Why does the OCR preset fail to download fonts or dicts?"

## Core workflow
1. Prefer `PaddleCV(task_name=...)` when the workflow matches a bundled preset.
2. Use `PaddleCV(config_path=...)` when the exact system DAG is not exposed as a task name.
3. Use `scripts/run_predict.py --task-name ... --input ...` for a bundled command-line route.
4. Use `PaddleCV.list_all_supported_tasks()` to discover the packaged task names.

## System task families
- OCR: `PP-OCRv2`, `PP-OCRv3`
- OCR extensions: `PP-OCRv3-IE`, `PP-OCRv3-SA`, `PP-OCRv3-TTS`
- Structure: `PP-Structure` plus direct config variants for table, layout-table, ser, and re
- Retrieval / recognition: `PP-ShiTu`, `PP-ShiTuV2`
- Analysis: `PP-Human`, `PP-Human-Attr`, `PP-Vehicle`, `PP-Vehicle-Attr`, `Face-Detection-Attr`
- Pose: `PP-TinyPose`

## Notes on dependencies
- `paddlenlp` and `paddlespeech` are part of the import surface because their operators are imported when `paddlecv` loads.
- `PaddleCV` uses `paddlecv://` URLs for configs, models, fonts, and dictionaries.
- OCR and structure workflows often depend on cache-populated fonts and label dictionaries.

## Common failure modes
- Task-name typo or stale catalog entry.
- Missing cache assets for config/model/font downloads.
- Speech or NLP import failures caused by dependency version mismatches.
- Incorrect input type for video, directory, or image-based presets.

## When to hand off
If the request is about one-model image inference, use `single-model-inference`. If the request is about building or changing the graph, operators, or output classes, use `custom-ops`.
