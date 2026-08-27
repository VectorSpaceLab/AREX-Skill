---
name: training-evaluation
description: "Guides safe MapTR training and chamfer-evaluation command
  construction, preflight validation, checkpoint handling, reproducibility, and
  resource-aware recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MapTR Training And Evaluation

Use this sub-skill to construct and review commands for MapTR training or
vector-map evaluation. It is deliberately conservative: prove inputs and
backend readiness before starting GPU work, prefer dry runs, and never infer
that a documented command succeeded on the current system.

## Scope And Evidence Status

This guidance covers the MapTR `main` behavior represented by commit
`a6872d8d9670bde17b4b01560f1221f88b443d55`:

- single-process and one-node distributed training;
- one-node distributed test/evaluation with the MapTR `chamfer` metric;
- work directories, seeds, deterministic mode, resume, FP16 configuration,
  checkpoints, result directories, and failure recovery.

The project documents Python 3.8, PyTorch 1.9.1 with CUDA 11.1,
`mmcv-full==1.4.0`, `mmdet==2.14.0`, `mmsegmentation==0.14.1`, the bundled
mmdetection3d 0.17.2 code, and a compiled GeometryKernelAttention extension.
Those are **documented compatibility targets**, not proof that a current host
can import the plugin or run its CUDA kernels. Full data, checkpoints,
training, evaluation, and the custom extension were not executed while this
skill was produced.

## Route First

- For nuScenes/AV2 download, conversion, annotation files, and directory
  layouts, route to `data-preparation`.
- For architecture selection, BEV/query settings, losses, or config authoring,
  route to `model-configuration`.
- For image/video rendering, qualitative output, or log plotting, route to
  `visualization-benchmarking`.
- Stay here for command semantics, launch sizing, metric selection,
  checkpoint/output behavior, and run-time troubleshooting.

## Required Run Contract

Before constructing a launch, obtain all of these values. Keep an unknown as a
stop condition rather than filling it with a guess.

1. **Intent:** train, resume training, or evaluate.
2. **Config:** exact MapTR config and any `--cfg-options` overrides.
3. **Data:** dataset family and proof that every configured annotation/map file
   and camera asset exists.
4. **Weights:** required backbone initialization for a new run, or the exact
   resume/evaluation checkpoint.
5. **Backend:** compatible legacy OpenMMLab stack, CUDA, `mmcv-full` ops, and
   GeometryKernelAttention import/build evidence.
6. **Resources:** visible GPU count, memory per GPU, requested process count,
   storage, wall-time, and scheduler rules.
7. **Outputs:** unique `--work-dir`, checkpoint retention plan, and evaluation
   result location.
8. **Reproducibility:** seed, deterministic policy, final merged config, source
   revision, and environment inventory.

Read [workflows.md](references/workflows.md) for complete gates, commands, and
expected observations. Read [cli-reference.md](references/cli-reference.md)
before adding flags or overrides.

## Safe Command Procedure

### 1. Stop Before Compute

From the MapTR project root, run only parser/config checks first:

```bash
python tools/train.py --help
python tools/test.py --help
python tools/misc/print_config.py projects/configs/maptr/maptr_tiny_r50_24e.py
```

The config print should show `plugin=True`, MapTR dataset/model types,
`evaluation.metric='chamfer'`, and resolved data/checkpoint paths. Printing a
config does not import the plugin, read all data, build CUDA extensions, or
prove training readiness.

Do not proceed when a path is missing, an override is unclear, requested GPUs
exceed visible GPUs, the config/checkpoint pairing is unverified, or a required
CUDA/custom-op probe has not passed.

### 2. Select The Smallest Launch

For a supported single-process training attempt:

```bash
python tools/train.py CONFIG.py \
  --work-dir work_dirs/RUN_ID \
  --gpus 1 --seed 42 --deterministic --launcher none
```

For one-node distributed training, use the bundled validator from this
sub-skill directory. It prints a command by default and starts nothing:

```bash
python scripts/launch_distributed.py train \
  --project-root MAPTR_ROOT --config projects/configs/maptr/CONFIG.py \
  --gpus N -- --work-dir work_dirs/RUN_ID --seed 42
```

For evaluation, use the same validator even with one GPU. The checked-in test
entry point intentionally rejects `--launcher none`:

```bash
python scripts/launch_distributed.py test \
  --project-root MAPTR_ROOT --config projects/configs/maptr/CONFIG.py \
  --checkpoint work_dirs/RUN_ID/epoch_N.pth --gpus N
```

The test command appends `--eval chamfer`. Never substitute the generic
3D-detection `bbox` launcher for MapTR. The vector-map datasets accept
`chamfer` and `iou`; project train/eval instructions and MapTR configs use
`chamfer`.

Review [launch_distributed.py](scripts/launch_distributed.py), then add
`--execute` only after its dry-run output and warnings pass human review.
Execution can allocate GPUs and run for hours.

### 3. Preserve Run Evidence

A training work directory should receive the merged config, timestamped text
log, logger outputs, and checkpoints such as `epoch_1.pth` according to
`checkpoint_config.interval`. MapTR 24-epoch configs normally evaluate every
two epochs and save every epoch. Confirm actual config values rather than
assuming those intervals for another config.

Chamfer evaluation should print per-class AP at thresholds 0.5, 1.0, and 1.5,
plus `NuscMap_chamfer/mAP`-style detail keys, and write formatted predictions
below a timestamped `test/<config-name>/` directory. Treat those as expected
shapes only, not benchmark claims.

Record the exact command, `CUDA_VISIBLE_DEVICES`, seed, deterministic flag,
merged config, checkpoint identity, environment versions, and complete log.
Do not compare scores from different configs, class maps, point sampling, data
versions, or checkpoints as if they were equivalent.

## High-Risk Semantics

- `--resume-from` restores training state; a nonexistent path is silently not
  applied by the training entry point. Validate it before launch.
- A backbone `pretrained` path initializes a new model; it is not a training
  resume checkpoint. `load_from` loads weights without promising optimizer and
  epoch continuity.
- Most MapTR configs enable static FP16 with `loss_scale=512`. Confirm the
  merged config and backend support. Do not add a second AMP mechanism.
- The distributed training wrapper forces deterministic mode. Determinism may
  reduce speed and does not guarantee bitwise identity across different GPU,
  driver, CUDA, library, or process-count combinations.
- `tools/test.py --out` is parsed but reaches an intentional assertion instead
  of dumping predictions. `--show`/`--show-dir` are not forwarded through its
  distributed test path. Route artifact visualization elsewhere.

## Recovery

Use [troubleshooting.md](references/troubleshooting.md) for symptoms, causes,
recovery, and explicit stop conditions. In particular:

- `metric bbox is not supported` → replace `--eval bbox` with
  `--eval chamfer`; do not reinterpret a detector metric as a map metric.
- eight requested processes with one visible GPU → stop and use `--gpus 1`, or
  move to a proven eight-GPU host; never oversubscribe silently.
- resume/config mismatch → stop, locate the config dumped beside the
  checkpoint, reconcile its model/data/class/optimizer/runner settings, and
  resume with that config or start a clearly new run.

Do not run merely to discover whether a prerequisite was satisfied. If
configuration, data, checkpoint provenance, backend compatibility, GPU count,
or budget remains unresolved, return a blocked preflight with the missing
evidence and the next safe probe.
