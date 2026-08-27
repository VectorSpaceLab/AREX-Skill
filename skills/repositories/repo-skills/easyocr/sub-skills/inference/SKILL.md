---
name: inference
description: "Run EasyOCR on images and image-like inputs with the Reader API or
  CLI, including batching, box extraction, and output formatting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# EasyOCR Inference

Use this sub-skill for ordinary OCR work: read text from an image, screenshot,
scan, crop, or batch of same-sized images with EasyOCR's built-in models.

## Use when

- The user wants text extracted from an image or screenshot.
- The task mentions `readtext`, `detect`, `recognize`, or `readtext_batched`.
- The task mentions the EasyOCR CLI.
- The user wants boxes, paragraphs, `detail=0`, JSON/dict output, or
  allowlist/blocklist filtering.

## Do not use when

- The user is loading a custom recognition bundle. Use `sub-skills/custom-models/`.
- The user is enabling DBNet or compiling DCN. Use `sub-skills/dbnet/`.
- The task is training or ONNX export. Those are out of scope for this skill.

## Quick workflow

1. Confirm the language codes and backend choice with
   `../../references/configuration.md`.
2. Run `../../scripts/inspect_runtime.py` if you want a fast install/backends smoke
   before a real OCR call.
3. Use `scripts/readtext_smoke.py` for a single-image OCR sanity check.
4. Read `references/workflows.md` for end-to-end patterns.
5. Read `references/troubleshooting.md` when the result or CLI behavior looks
   wrong.

## Typical inputs and outputs

- Inputs: file path, NumPy array, raw bytes, or a raw image URL.
- Outputs: strings, `(box, text, confidence)` tuples, dicts, or JSON strings,
  depending on `detail` and `output_format`.
- `readtext_batched` returns one OCR result list per input image.
- `detect` returns boxes first; `recognize` consumes boxes or a full crop.

## Common control points

- `gpu`: automatic accelerator selection or explicit CPU/device choice.
- `download_enabled`: whether missing model files may be downloaded.
- `paragraph`, `rotation_info`, `allowlist`, `blocklist`, `detail`, and
  `output_format`.
- `batch_size` and `workers` for throughput tuning.

## References and scripts

- `../../references/api-reference.md` for public signatures and return shapes.
- `../../references/cli-reference.md` for the CLI flag groups and parser
  caveats.
- `../../references/configuration.md` for cache paths, backend behavior, and
  language/model rules.
- `references/workflows.md` for practical OCR examples.
- `references/troubleshooting.md` for CLI quirks, model-cache issues, and
  legacy helper caveats.
- `scripts/readtext_smoke.py` for a tiny OCR run against one image.

## Boundary notes

- Keep custom bundle loading, detector compilation, and training guidance in
  their owning sub-skills.
- Prefer the Python API for exact control when the CLI's current parser quirks
  make a flag hard to use reliably.
