---
name: conversion
description: "Convert OpenMMLab/PyTorch models with MMDeploy, including IR
  export, deploy.py workflows, ONNX partitioning, calibration, quantization, and
  work-dir artifact interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDeploy conversion sub-skill

Use this sub-skill when a user needs to convert an OpenMMLab/PyTorch model with MMDeploy: selecting the deploy config, model config, checkpoint, sample input, work directory, target device, IR type, partition policy, calibration source, quantization mode, and interpreting generated artifacts.

## Route by task

- For an end-to-end CLI conversion, start with [references/workflows.md](references/workflows.md) and the bundled [scripts/deploy.py](scripts/deploy.py).
- For direct Python API calls, signatures, and backend/PyTorch visualization routing, use [references/api-reference.md](references/api-reference.md).
- For deploy config authoring or diagnosing shape/precision/codebase fields, use [references/configuration.md](references/configuration.md).
- For failed conversions, missing marks, calibration issues, backend handoff errors, or CLI/API misuse, use [references/troubleshooting.md](references/troubleshooting.md).

## Owned responsibilities

- Choose and validate `deploy_cfg`, `model_cfg`, checkpoint, input image/data, `--work-dir`, `--device`, `--test-img`, and SDK metadata dump options.
- Run the deployment pipeline that exports ONNX or TorchScript IR, partitions ONNX by marks, creates calibration HDF5 data, converts IR files to backend files, and renders comparison outputs when possible.
- Explain `--dump-info`, `--show`, `--quant`, `--quant-image-dir`, and `--calib-dataset-cfg` behavior.
- Explain work-dir artifacts such as `end2end.onnx`, TorchScript files, backend engine files, partitioned ONNX files, `calib_data.h5`, `deploy.json`, `pipeline.json`, `detail.json`, `output_<backend>.jpg`, and `output_pytorch.jpg`.

## Boundaries and handoffs

- Backend installation, custom backend build steps, shared-library/plugin setup, and hardware readiness belong to the backend guidance, not this sub-skill. This sub-skill identifies the backend requirement and the failing handoff point.
- SDK runtime inference and packaged demo usage belong to SDK guidance. This sub-skill only explains how `--dump-info` writes SDK metadata during conversion.
- Rewriter implementation belongs to extensibility guidance. This sub-skill covers only partition marks, `partition_config`, and `extract_model` inputs/outputs.
- Validation, benchmarking, regression suites, and accuracy evaluation belong to validation guidance after conversion artifacts exist.

## Operating guardrails

1. Require explicit user-supplied paths for the deployment config, upstream model config, checkpoint, representative conversion input, and work directory.
2. Confirm that the target OpenMMLab codebase is importable before blaming MMDeploy conversion logic.
3. Match device to backend: TensorRT needs a CUDA device such as `cuda:0`; OpenVINO is CPU-oriented; other backends have their own device/runtime requirements.
4. Use a fresh work directory for each conversion attempt to avoid stale IR/backend files being mistaken for current outputs.
5. Do not treat a successful IR export as proof that backend conversion or SDK runtime is usable; inspect backend files and hand off backend/runtime failures to the appropriate sub-skill.
