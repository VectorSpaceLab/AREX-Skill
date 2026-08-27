---
name: data-formats
description: "Validates OFA TSV rows, selected-column layouts, base64 image
  payloads, code sequences, and speech manifests before GPU runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-formats

Use this sub-skill when a user needs to prepare, inspect, or validate OFA input files before launching a task.

## Trigger phrases

- "What columns does this TSV need?"
- "Why does the data loader crash on this row?"
- "How do I base64-encode OFA images?"
- "Is my VQA / RefCOCO / OCR / MMSpeech manifest correct?"
- "Can you validate the pretraining workspace first?"

## What this sub-skill owns

- OFA TSV row layouts and selected-column rules,
- base64 image payload checks,
- image-code sequence validation,
- answer-label and reference-field sanity checks,
- manifest/file-path validation for speech workflows,
- safe preflight checks for pretraining data bundles.

## What it excludes

- the training/evaluation command itself -> the task sub-skill,
- model internals and registration -> `model-internals-and-extension`,
- generic image manipulation unrelated to OFA TSVs -> other vision skills.

## Read these files

- [references/data-formats.md](references/data-formats.md) for row layouts and validation cues.
- [references/troubleshooting.md](references/troubleshooting.md) for common row-shape failures.
- [scripts/encode_image_base64.py](scripts/encode_image_base64.py) to convert a local image into a TSV-safe payload.
- [scripts/validate_ofa_tsv.py](scripts/validate_ofa_tsv.py) for general TSV checks.

## Typical workflow

1. Identify the task family.
2. Confirm the expected row width and selected columns.
3. Validate base64, image, code, JSON, or path cells.
4. Only then hand the file to the workflow sub-skill for a training or evaluation command.

## Notes

- Many OFA workflows use a tab-separated flat file instead of a dataset library format.
- The same base64 image can appear in caption, VQA, RefCOCO, OCR, and image-generation layouts.
- Selected columns matter as much as the row content; a row can look valid but still feed the wrong task.
