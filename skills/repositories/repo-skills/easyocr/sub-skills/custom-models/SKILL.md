---
name: custom-models
description: "Load EasyOCR custom recognition bundles, validate the file triad,
  and configure custom model and user-network directories."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# EasyOCR Custom Models

Use this sub-skill when the user has a custom recognition bundle and wants to
load it with EasyOCR instead of the built-in recognition models.

## Use when

- The task mentions `recog_network='custom_example'` or another custom stem.
- The user has `.pth`, `.yaml`, and `.py` files for a custom recognizer.
- The task is about `user_network_directory`, `model_storage_directory`, or
  `EASYOCR_MODULE_PATH`.
- The user wants to check whether a bundle is complete before running OCR.

## Do not use when

- The user wants to train the model. That is out of scope here.
- The user wants DBNet or detector compilation. Use `sub-skills/dbnet/`.
- The task is ordinary OCR with built-in models. Use `sub-skills/inference/`.

## Quick workflow

1. Read `references/workflows.md` for the bundle layout and load sequence.
2. Run `scripts/check_bundle.py` against the custom bundle directory or stem.
3. Confirm that the stem is the same across `.pth`, `.yaml`, and `.py`.
4. Load the bundle with `easyocr.Reader(..., recog_network='<stem>')`.
5. Read `references/troubleshooting.md` if the bundle fails to load.

## What this sub-skill owns

- The custom recognition bundle triad.
- Directory layout for user networks and model weights.
- The `Reader` constructor path that loads custom recognition code.
- Fast bundle validation before runtime.

## References and scripts

- `../../references/api-reference.md` for the main `Reader` signature.
- `../../references/configuration.md` for cache directories and environment
  variable precedence.
- `references/workflows.md` for the bundle file layout and load pattern.
- `references/troubleshooting.md` for stem mismatches, YAML errors, and
  import failures.
- `scripts/check_bundle.py` for a safe bundle validator.

## Boundary notes

- Keep training, dataset creation, and maintainer-only language regeneration
  out of this sub-skill.
- If the task needs a different detector backend, route to the DBNet sub-skill.
- If the task only needs built-in languages, route to inference instead.
