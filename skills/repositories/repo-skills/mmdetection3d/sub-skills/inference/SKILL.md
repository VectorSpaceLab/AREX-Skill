---
name: inference
description: "Run and adapt MMDetection3D point-cloud, monocular,
  multi-modality, and lidar segmentation inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDetection3D inference sub-skill

Use this sub-skill when the user needs to run, modify, or troubleshoot MMDetection3D inference for:

- LiDAR / point-cloud 3D detection.
- Monocular image 3D detection.
- LiDAR + image multi-modality 3D detection.
- LiDAR point-cloud semantic segmentation.
- Python API calls through `mmdet3d.apis` or the 3D inferencer classes.

This sub-skill is intentionally safe by default: the bundled script only renders commands and never loads models, checkpoints, datasets, GPUs, or visualizers.

## Start here

1. Identify the task type:
   - `lidar-det`: point-cloud detection.
   - `mono-det`: monocular image detection with an annotation/info file.
   - `multi-modality-det`: point cloud plus image(s) with an annotation/info file.
   - `lidar-seg`: point-cloud segmentation.
2. Confirm the user has a matching config and checkpoint for the same model family, dataset, classes, and task.
3. For demo-style command construction, use [`scripts/build_inference_command.py`](scripts/build_inference_command.py). It prints a shell command only.
4. For Python integration, use [`references/api-reference.md`](references/api-reference.md) to choose between low-level API functions and inferencer classes.
5. For output, visualization, remote-server, and batch workflow choices, use [`references/workflows.md`](references/workflows.md).
6. For failures, use [`references/troubleshooting.md`](references/troubleshooting.md).

## Route away

- Dataset conversion, dataset root layout, or annotation/info generation belongs in the data-preparation sub-skill.
- Config-family selection, model zoo alias lookup, or config mutation belongs in the configuration-model-zoo sub-skill.
- Training, testing, metric evaluation, TTA, or distributed launch belongs in the training-evaluation sub-skill.
- Geometry objects, coordinate conversions, box projection, or visualization internals belong in the structures-visualization sub-skill.
- TorchServe, model publishing, FLOPs, or log-analysis utilities belong in the serving-tools sub-skill.

## Minimal operating rules

- Do not run an inference command unless the user explicitly asks for model execution and accepts the hardware/checkpoint/runtime cost.
- Prefer no-display-safe commands on remote servers: omit `--show`, keep an `--out-dir`, and save predictions.
- Demo commands are file-path workflows. For in-memory arrays, use the inferencer classes where supported; see the ndarray limitations in [`references/api-reference.md`](references/api-reference.md).
- Treat checkpoint URLs and model aliases as potentially network-triggering during actual execution. The bundled command builder does not download anything.
- Always preserve the user's config/checkpoint pairing unless they ask for model-family changes.
