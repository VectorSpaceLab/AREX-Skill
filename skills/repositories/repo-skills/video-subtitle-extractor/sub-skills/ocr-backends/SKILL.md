---
name: ocr-backends
description: "Configure and troubleshoot VSE PaddleOCR models, language codes,
  thresholds, and CPU/CUDA/DirectML/ONNX backend acceleration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OCR Backends

Use this sub-skill for VSE OCR setup: PaddlePaddle/PaddleOCR installs, bundled
PP-OCRv5 model selection, language codes, CPU/GPU/ONNX provider choices,
recognition batches, confidence thresholds, and backend verification.

## Read first

- [model and language reference](references/model-and-language-reference.md)
  for language groups, Fast/Auto/Accurate model directories, and V5 names.
- [backend compatibility](references/backend-compatibility.md) for CPU, CUDA,
  DirectML, ONNX, and unsupported/new-GPU decisions.
- [API reference](references/api-reference.md) for `OcrRecogniser`,
  `SubtitleDetect`, `PaddleModelConfig`, and `HardwareAccelerator`.
- [troubleshooting](references/troubleshooting.md) for import/model/provider
  errors and low confidence.
- Run [scripts/model_config_probe.py](scripts/model_config_probe.py) or
  [scripts/hardware_backend_probe.py](scripts/hardware_backend_probe.py) for
  safe read-only diagnostics.

## Key decisions

- Choose CPU unless the user has a verified accelerator and backend-specific
  Paddle/ONNX packages.
- `fast` mode prefers mobile detection and mobile recognition for Chinese,
  Traditional Chinese, English, and Japanese; other languages use language
  group recognizers.
- `auto` and `accurate` use server detection; Chinese/English/Japanese use
  server recognition, while many non-CJK languages use grouped mobile
  recognizers.
- Do not treat a visible GPU as proof that VSE uses it. Verify Paddle compiled
  CUDA or ONNX providers.

## Route elsewhere

- Extraction sequencing, VideoSubFinder, output/caches: [extraction-workflows](../extraction-workflows/SKILL.md).
- GUI settings cards for these options: [gui-batch-operations](../gui-batch-operations/SKILL.md).
- Text cleanup and typo replacement after OCR: [postprocessing-config](../postprocessing-config/SKILL.md).
