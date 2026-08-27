---
name: models-and-customization
description: "Use docTR standalone model factories, custom weights, vocabulary
  whitelists, Hugging Face Hub models, ONNX export, and PyTorch
  device/precision/compile optimization safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# models-and-customization

Use this sub-skill when the task is about docTR model selection or model-level customization rather than end-to-end document I/O:

- Choosing detection, recognition, layout, table, classification, crop-orientation, or page-orientation architectures.
- Instantiating standalone predictors such as `detection_predictor`, `recognition_predictor`, `layout_predictor`, `table_predictor`, `crop_orientation_predictor`, and `page_orientation_predictor`.
- Loading custom weights or custom trained models into docTR predictors.
- Restricting recognition outputs with vocabulary whitelists.
- Loading or sharing models through the Hugging Face Hub interface.
- Exporting PyTorch models to ONNX or optimizing inference with devices, batch sizes, half precision, or `torch.compile`.

Do not use this sub-skill as the primary guide for full OCR/KIE pipelines, document loading/export objects, dataset formats, training commands, CLI usage, or service deployment. Route those to the corresponding sibling sub-skill, then return here only for the model-level details.

## Operating procedure

1. Start with [references/model-catalog-and-customization.md](references/model-catalog-and-customization.md) to pick the correct architecture, factory signature, custom loading pattern, Hub entry point, or whitelist strategy.
2. Use [references/optimization-and-export.md](references/optimization-and-export.md) before changing devices, precision, compile mode, batch sizes, or ONNX export settings.
3. If anything fails, read [references/troubleshooting.md](references/troubleshooting.md) before changing architectures or assuming a package bug.
4. Keep user code explicit about `pretrained`: `pretrained=True` can trigger model downloads; `pretrained=False` creates randomly initialized models and is not useful for real inference unless weights are loaded afterward.

## Quick routing cues

- "Which architecture should I use?" → model catalog.
- "I trained weights; how do I plug them into docTR?" → custom loading section in the model catalog.
- "Only allow German/Latin characters" → whitelist section in the model catalog.
- "Use a model from Hugging Face" → Hub section in the model catalog.
- "CUDA, MPS, BF16, FP16, compile, ONNX" → optimization/export reference.
- "Unknown architecture, state dict mismatch, CPU half precision, ONNX shape/names" → troubleshooting reference.
