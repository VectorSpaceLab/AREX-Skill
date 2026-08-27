---
name: deployment
description: "Routes single-model DeepStream-Yolo build, config editing, and
  runtime deployment tasks for one detector."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deployment

Use this sub-skill when the task is about one DeepStream YOLO pipeline end to end: building the custom inference library, choosing the right config template, editing the DeepStream app config, and diagnosing build or runtime failures.

## Trigger phrases

- build the DeepStream-Yolo library
- run one YOLO model in DeepStream
- edit `config_infer_primary*.txt`
- edit `deepstream_app_config.txt`
- custom model on `deepstream-app`
- why does the pipeline not start
- how do I map labels or class counts

## Include here

- `CUDA_VER` selection for the chosen DeepStream release.
- `make -C nvdsinfer_custom_impl_Yolo ...` build flow.
- `deepstream_app_config.txt` and single `primary-gie` wiring.
- Custom models that already have `.onnx` or `.cfg` / `.weights` artifacts.
- Model-family config differences that affect a single detector.
- Cross-cutting deployment troubleshooting.

## Exclude or route elsewhere

- Exporting checkpoints to ONNX: use `model-conversion`.
- Multiple primary/secondary detectors: use `multi-gie`.
- INT8 calibration tuning and benchmark interpretation: use `int8-benchmarking`.
- Repo maintenance, import/export to other agents, or refresh logic.

## How to use this route

1. Read `references/workflows.md` for the full single-model flow.
2. Read `references/configuration.md` before editing any config template.
3. Run `scripts/check-deepstream-toolchain.sh` to see whether the host is ready for build/runtime work.
4. Run `scripts/build-nvdsinfer-plugin.sh --output-dir ./deepstream-yolo-runtime` once `CUDA_VER` is set; the helper stages the bundled parser source and configs for you.
5. Launch `deepstream-app` from the staged runtime tree, not from the original repository checkout.
5. Use `references/troubleshooting.md` if the build or runtime fails.

## Key decisions

- If the model is still a checkpoint, route to `model-conversion` first.
- If the model is already an ONNX file or Darknet pair, this sub-skill owns the DeepStream wiring.
- If the same app needs two or more detectors, route to `multi-gie` instead of piling secondary configuration into this route.

## What a future agent should be able to do here

- Identify the correct config template for the model family.
- Set the right `batch-size`, `network-mode`, `num-detected-classes`, and parser / engine creator names.
- Distinguish Darknet-style `custom-network-config` from ONNX-style `onnx-file` configs.
- Recognize whether the failure is a build issue, a model/template mismatch, or a host prerequisite gap.

## Common failure signals

- `CUDA_VER is not set`
- `deepstream-app: command not found`
- Missing or mismatched `labels.txt`
- Wrong `num-detected-classes`
- Engine file created for the wrong batch size or precision
- `GLib` or GStreamer runtime issues on the host

## Linked helpers

- `scripts/check-deepstream-toolchain.sh` — probe build/runtime readiness.
- `scripts/build-nvdsinfer-plugin.sh` — wrapper for the custom library build.
- `references/workflows.md` — the single-model step-by-step flow.
- `references/configuration.md` — the config key table and model-family notes.
- `references/troubleshooting.md` — deployment-specific symptoms and fixes.
