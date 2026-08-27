---
name: dbnet
description: "Use EasyOCR's DBNet detector, check DBNet import/init, and compile
  the DCN operator when the detector backend needs repair."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# EasyOCR DBNet

Use this sub-skill when the task involves `detect_network='dbnet18'`, DBNet
import/init, or compiling the DCN operator that DBNet needs.

## Use when

- The user wants the DBNet detector instead of the default CRAFT detector.
- The user asks about `DBNet`, `dcn`, `compile`, `NVCC`, or CUDA/CPU build
  issues.
- A DBNet import works but initialization or detection fails.
- The user needs a quick CPU smoke for the DBNet module.

## Do not use when

- The task is ordinary OCR with the default detector. Use
  `sub-skills/inference/`.
- The task is about custom recognition bundles. Use
  `sub-skills/custom-models/`.
- The task is only about training or ONNX export.

## Quick workflow

1. Read `references/workflows.md` for the DBNet runtime and compile sequence.
2. Run `scripts/compile_dcn.py --help` or `--check-only` to inspect the current
   DCN state.
3. If needed, run `scripts/compile_dcn.py --build` after checking the compiler
   prerequisites.
4. Use `references/troubleshooting.md` for device mismatch, missing operator,
   and compiler failures.

## What this sub-skill owns

- DBNet detector selection inside EasyOCR.
- DBNet import/init checks.
- DCN operator build and presence checks.
- CPU versus CUDA compilation guidance for the DBNet operator.

## References and scripts

- `../../references/api-reference.md` for the main `Reader` surface.
- `../../references/configuration.md` for cache locations and detector choice.
- `references/workflows.md` for DBNet runtime and compile steps.
- `references/troubleshooting.md` for backend, operator, and device errors.
- `scripts/compile_dcn.py` for a bundled DCN helper.

## Boundary notes

- Keep the default detector workflow in inference.
- Keep custom model loading in the custom-models sub-skill.
- Treat `dbnet50` as an internal DBNet detail here; `Reader` only exposes the
  DBNet choice used in this checkout.
