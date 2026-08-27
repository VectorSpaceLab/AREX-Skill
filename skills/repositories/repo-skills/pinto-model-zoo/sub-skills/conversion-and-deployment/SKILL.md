---
name: conversion-and-deployment
description: "Plan PINTO_model_zoo model conversion, quantization, and backend
  deployment workflows from bundled catalog evidence and local script
  inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# conversion-and-deployment

Use this sub-skill when the user asks how to convert, quantize, or deploy a
PINTO_model_zoo model artifact across ONNX, TensorFlow/SavedModel, TFLite,
OpenVINO, CoreML, TensorFlow.js, TF-TRT, or EdgeTPU-oriented backends.

Typical triggers:

- "convert this ONNX model to TFLite/OpenVINO/CoreML/TFJS"
- "make an INT8/full-integer/FP16/TFLite/EdgeTPU artifact"
- "understand this quantization or conversion script"
- "deploy this model on Raspberry Pi, OpenVINO CPU, browser TFJS, TF-TRT, or EdgeTPU"
- "why do I need calibration data or a representative dataset?"

## Route before planning

1. If the user has not selected a model, route model search and format
   availability to `model-catalog` and the bundled catalog at
   `../../references/model-catalog.json`.
2. If a needed artifact is not present locally, route download/script safety and
   license checks to `model-acquisition` before proposing commands that fetch or
   unpack files.
3. If the user wants to run inference, benchmark, or smoke-test an artifact,
   route execution planning to `inference-demos` after this skill identifies the
   target backend and artifact constraints.
4. Stay in this skill for conversion-chain selection, quantization requirements,
   calibration gates, backend deployment preflight, and conversion-script
   diagnosis.

## Operating workflow

1. **Pin the source and target.** Record current artifact family, desired target
   family, precision goal, input shape/layout/color order, deployment hardware,
   and whether network/dataset/hardware use is approved.
2. **Prefer an existing zoo artifact.** If the catalog already lists the target
   format flag for the selected model, advise using that artifact before
   rebuilding it. Treat catalog flags as availability evidence, not proof that a
   shallow checkout already contains the files.
3. **Inspect local scripts without executing them.** Use
   `scripts/classify_conversion_script.py` on candidate `convert*.sh`,
   `*quant*.py`, `*tflite*.py`, `*openvino*.py`, `*coreml*.py`, or similar files
   in the selected model directory. The helper reports conversion families,
   representative-dataset requirements, and dataset/network/hardware risks.
4. **Choose a recipe.** Use `references/conversion-recipes.md` for format-family
   constraints, TFLite quantization modes, ONNX/TensorFlow/OpenVINO/CoreML/TFJS/
   TF-TRT chains, and calibration stop conditions.
5. **Preflight the backend.** Use `references/deployment-backends.md` for
   Raspberry Pi/TFLite, EdgeTPU, OpenVINO CPU, browser TFJS/WebGL, TF-TRT/GPU,
   and CoreML deployment gates.
6. **Stop instead of guessing** when required calibration data, network access,
   large datasets, proprietary hardware, GPU/EdgeTPU devices, or license approval
   is absent. Provide the smallest safe next check and mark unverified hardware
   claims explicitly.

## Expected answer shape

For user-facing plans, return:

- selected source artifact and target artifact family;
- whether a catalog artifact already appears available;
- conversion chain with required tools/environments named only at the family
  level unless the selected folder supplies exact scripts;
- calibration or representative-dataset requirements;
- backend preflight and stop gates;
- smoke-test handoff to `inference-demos` when execution is requested;
- open risks from `references/troubleshooting.md`.

## Owned failure modes

This sub-skill owns troubleshooting for conversion, quantization, calibration,
and backend deployment errors. Use `references/troubleshooting.md` when symptoms
include missing converter imports, unsupported TFLite/EdgeTPU ops, representative
sample mismatch, OpenVINO XML/BIN mismatch, browser TFJS loading issues, TF-TRT
GPU/runtime mismatch, or hardware-only verification claims.
