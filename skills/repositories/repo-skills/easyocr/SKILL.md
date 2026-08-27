---
name: easyocr
description: "Use EasyOCR to detect and recognize text in images, configure
  model and language selection, load custom recognition bundles, and
  troubleshoot DBNet setup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# EasyOCR

Use this skill when the task is about extracting text from images, screenshots,
scans, or cropped regions with EasyOCR.

## Start here

1. Install EasyOCR together with a PyTorch build that matches your backend.
   For CPU-only use, a normal `pip install easyocr` is usually enough.
   For GPU runs, install the matching `torch` and `torchvision` wheels first.
2. Run `scripts/inspect_runtime.py` to confirm the package imports and the
   backend choice without downloading model weights.
3. Pick the right route:
   - `sub-skills/inference/` for ordinary OCR API or CLI usage.
   - `sub-skills/custom-models/` for custom recognition bundles or custom
     model directories.
   - `sub-skills/dbnet/` for `detect_network='dbnet18'`, DBNet import/init,
     or DCN compilation issues.

## What this skill covers

- `easyocr.Reader` initialization and the main OCR methods.
- Language selection, model cache locations, download behavior, and backend
  fallback.
- The EasyOCR CLI entry point.
- Custom recognition model loading.
- DBNet detector setup and DCN operator compilation.

## What this skill does not cover

- Training a new OCR model from scratch.
- ONNX export helpers.
- Maintainer-only language regeneration or release automation.

## Quick import check

```bash
python -c "import easyocr; print(easyocr.__version__)"
python scripts/inspect_runtime.py --help
```

## Route map

- Read `references/api-reference.md` for public signatures and output shapes.
- Read `references/cli-reference.md` for the CLI flag groups and parser
  caveats.
- Read `references/configuration.md` for environment variables, cache paths,
  backend selection, and model selection rules.
- Read `references/troubleshooting.md` for install, import, model-cache, and
  CLI/runtime quirks.
- Read `references/repo-provenance.md` to check the source commit, package
  version, and refresh baseline.
- Use `sub-skills/inference/` for normal image OCR.
- Use `sub-skills/custom-models/` for custom recognition bundles.
- Use `sub-skills/dbnet/` for DBNet detector setup and DCN compilation.

## Common user intents

- "Read text from this image" -> `sub-skills/inference/`
- "Use my own recognition model" -> `sub-skills/custom-models/`
- "Enable DBNet" or "compile DCN" -> `sub-skills/dbnet/`
- "EasyOCR import fails" -> `references/troubleshooting.md`

## Notes for future agents

- Prefer the bundled scripts and references in this skill tree.
- Do not depend on the original repository checkout once the guidance has been
  distilled here.
- Treat `easyocr.Reader` and the CLI as the stable public surface; keep lower-
  level implementation details in the sub-skill references.
