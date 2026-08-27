---
name: training-and-inference
description: "Route legacy SECOND and PointPillars model construction, training,
  evaluation, checkpoint restoration, and inference with explicit configuration,
  device, and backend guards."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and inference

Use this sub-skill when a task asks to train or evaluate SECOND/PointPillars,
build a `VoxelNet`, restore a `.tckpt`, run inference, select a model config,
or reason about multi-GPU, fp16, NMS, or spconv errors.

## Safety and compatibility boundary

- This repository is deprecated. Its public README recommends OpenPCDet or
  MMDetection3D for new work; prefer a maintained implementation unless the
  historical checkpoint or experiment specifically requires this code.
- The detector route is **legacy-backend guarded and unverified**. Source code
  depends on old `spconv` APIs (`VoxelGeneratorV2` and NMS symbols), legacy
  Numba CUDA behavior, and an old PyTorch integration. A modern spconv 2.x
  import is not proof of compatibility.
- Run the bundled non-invasive probe before any detector import:
  `python <training-skill-root>/scripts/check_legacy_backend.py`.
  Add `--require-detector` only when deciding whether to attempt a detector
  route. Without it, the probe is diagnostic and returns success even when the
  legacy symbols are absent.
- CUDA availability, a successful CUDA tensor smoke test, or a CPU import does
  not prove that sparse model construction, NMS, training, or inference works.
  Do not claim detector execution was verified from those observations.
- This package has no setup metadata. Use an explicit, isolated environment
  only when a separately supplied compatible checkout is intentionally in
  scope. Do not assume a package install or silently mutate an existing
  environment. This skill does not bundle the historical detector entry point.

## Route the request

1. **Config/data contract:** choose a config and validate dataset paths,
   generated info/database files, class order, voxel range, and point feature
   count. Route dataset generation and layout preparation to
   [data-preparation](../data-preparation/SKILL.md).
2. **Model/training:** map `network_class_name`, VFE, middle extractor, and RPN
   names through the registries; use the Fire commands and output semantics in
   [workflows](references/workflows.md).
3. **Evaluation/geometry:** keep box encoding, NMS, score thresholds, and
   evaluator implementation questions with
   [geometry-and-evaluation](../geometry-and-evaluation/SKILL.md).
4. **Viewer/service:** route web API, browser, and server operations to
   [visualization-and-serving](../visualization-and-serving/SKILL.md); do not
   start the legacy viewer as a training smoke test.

## Reference map

- [workflows](references/workflows.md): Fire commands, guarded train/resume,
  multi-GPU scaling, evaluation outputs, inference, pretrained loading, and
  NuScenes tuning notes.
- [configuration](references/configuration.md): config families, protobuf
  fields, model registries, class order, optimizers, and schedules.
- [API reference](references/api-reference.md): public signatures, model
  methods, builder contracts, freeze filters, and torchplus checkpoints.
- [compatibility](references/compatibility.md): exact backend gate, known
  modern-spconv gaps, and evidence needed to widen executable scope.
- [troubleshooting](references/troubleshooting.md): install/import, optional
  dependencies, data/config, CLI/API, checkpoint, multi-GPU, fp16, and
  workflow-specific failures.

## Guarded command patterns

First run the bundled non-invasive probe:

```bash
python <training-skill-root>/scripts/check_legacy_backend.py
python <training-skill-root>/scripts/check_legacy_backend.py --require-detector
```

The second command is the detector gate. This skill does not bundle or invoke
that historical writer/runner, so no source-checkout command is presented as a
runnable recipe. If the probe reports missing legacy symbols, stop before any
historical `train`, `evaluate`, or `TorchInferenceContext` attempt; capture the
exact missing names and use [compatibility](references/compatibility.md) for
recovery. If a user separately supplies a compatible checkout, the historical
argument shapes are documented in [workflows](references/workflows.md).

These are guarded historical routes, not verified recipes. `train` refuses an
existing `model_dir` unless `--resume=True`; `--create_folder=True` creates a
new timestamped folder when the requested prefix already exists. Keep model
outputs outside the source tree and back up checkpoints before experiments.

## Core decisions

- `batch_size` and `num_workers` in the training input config are **per GPU**.
  The implementation multiplies both by the visible GPU count for
  `--multi_gpu=True`; do not multiply the config values yourself.
- The README says to divide `train_config.steps` and `steps_per_eval` by the
  number of GPUs when scaling a single-GPU schedule to multi-GPU. Verify this
  arithmetic before launching; an undivided schedule changes total optimizer
  updates and evaluation cadence.
- fp16 requires the historical Apex path and a compatible sparse backend;
  `enable_mixed_precision: true` is not equivalent to modern PyTorch AMP.
  Honor the source assertion that `max_number_of_voxels * batch_size < 65535`.
- `measure_time=True` enables CUDA synchronization/timers in model paths and
  can distort throughput. Use it only for a deliberate timing run.
- `evaluate` writes `result.pkl` below `<result-path>/step_<global_step>` and
  invokes the dataset evaluator. The historical signature does not accept the
  README-era `--pickle_result` keyword; do not pass it to a separately supplied
  runner unless its help output proves otherwise. Route official label
  conversion to geometry/evaluation after checking the exact dataset API.
- Checkpoints are named by model/optimizer plus step and indexed in
  `checkpoints.json`. Restore the latest compatible state, or pass an explicit
  `.tckpt`; never mix a checkpoint with an incompatible config.

For exact signatures, config fields, model registry names, checkpoint utilities,
and failure recovery, read the linked references before giving a detailed
command or API answer.
