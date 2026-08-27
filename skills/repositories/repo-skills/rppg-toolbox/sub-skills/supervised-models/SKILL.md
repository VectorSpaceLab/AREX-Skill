---
name: supervised-models
description: "Configure and safely extend rPPG-Toolbox supervised neural models
  for train_and_test or only_test runs, including tensor layouts, checkpoints,
  devices, and PhysMamba backend constraints."
disable-model-invocation: true
metadata: { disco-role: operating }
license: NOASSERTION
---

# Supervised models

Use this skill when a Researcher must select one of the toolbox's supervised
models, adapt a training or inference YAML, diagnose a checkpoint/device/shape
failure, or plan a safe model/trainer extension. The exact dispatch spellings,
model contracts, and known trainer caveats are in
[references/model-overview.md](references/model-overview.md). The run sequence
and checkpoint routing are in [references/workflows.md](references/workflows.md).

This skill does **not** prepare raw videos, face crops, cached arrays, or file
lists. Start with [data-preparation](../data-preparation/SKILL.md) for those
inputs. It does not select standalone signal-processing methods; use
[unsupervised-methods](../unsupervised-methods/SKILL.md). Send metrics, pickles,
and plots to [evaluation-and-visualization](../evaluation-and-visualization/SKILL.md).

## Dispatch contract

- `main.py` accepts these exact `MODEL.NAME` values in both `train_and_test`
  and `only_test`: `Physnet`, `iBVPNet`, `FactorizePhys`, `Tscan`,
  `EfficientPhys`, `DeepPhys`, `BigSmall`, `PhysFormer`, `PhysMamba`, and
  `RhythmFormer`. Names such as `PhysNet` or `TSCAN` are descriptive names, not
  accepted dispatch values; use `Physnet` and `Tscan` in YAML.
- `train_and_test` constructs the model-specific trainer, calls its `train`,
  then calls its `test`. `only_test` constructs the same trainer and calls only
  `test`; it never trains or creates a new checkpoint.
- Every supervised trainer is expected to expose `train`, `valid`, `test`, and
  `save_model`. `valid` is used for model selection only when
  `TEST.USE_LAST_EPOCH: false`. A missing validation dataset in that mode is a
  configuration error.
- Treat dataset preparation, a full training run, checkpoint loading, and
  evaluation as user-controlled and potentially expensive. This skill never
  downloads data/checkpoints, changes raw data, or launches training by itself.

## Fast configuration route

1. Choose the exact model spelling and read its row in
   [model-overview.md](references/model-overview.md). Do not start by changing
   the model name to match a paper title.
2. Reuse a matching train or inference YAML as a template, then replace every
   user path, dataset split, `DATA_FORMAT`, preprocessing type, chunk/frame
   depth, and `DEVICE`. Keep train/valid/test tensor geometry compatible.
3. Confirm the cache contract with data-preparation. Most 3-D models consume
   `N,C,T,H,W` after an `NCDHW` loader return; frame-wise 2-D models consume
   flattened `N*T,C,H,W` after an `NDCHW` return. BigSmall is a two-stream
   exception. Do not silently transpose a cache to hide a mismatch.
4. For `only_test`, set `INFERENCE.MODEL_PATH` to the user-controlled state-dict
   file and reproduce the architecture settings used to create it. For a
   trained run, leave `INFERENCE.MODEL_PATH` unused: the trainer selects an
   epoch from `MODEL.MODEL_DIR` and `TRAIN.MODEL_FILE_NAME`.
5. Run the non-writing smoke probe before a real run:
   `python scripts/model_smoke.py --model Tscan --device cpu`.
   Add `--forward` only with an explicitly supplied external model factory; the
   default probe is source-independent and never imports the checkout.
6. For predictions, configure the test metrics/window and optionally an output
   directory. Follow evaluation-and-visualization for pickle schema and metric
   interpretation.

## Device and checkpoint guardrails

- `DEVICE` is a single torch device such as `cpu` or `cuda:0`; do not pass a
  comma-separated device list to the smoke script or pretend a CPU run proves
  CUDA-only behavior. `NUM_OF_GPU_TRAIN` controls DataParallel in several
  trainers and must agree with visible hardware.
- Each epoch is saved as
  `<MODEL.MODEL_DIR>/<TRAIN.MODEL_FILE_NAME>_Epoch<zero-based-index>.pth`.
  With `TEST.USE_LAST_EPOCH: true`, train-and-test loads `EPOCHS - 1`; with it
  false, it loads the lowest-validation-loss epoch (BigSmall tracks
  `used_epoch`). A failed save or absent selected file is a hard stop.
- `only_test` loads `INFERENCE.MODEL_PATH`, not `TRAIN.MODEL_FILE_NAME`. A
  checkpoint is a state dict, not a full optimizer/trainer snapshot. DataParallel
  wrappers, model class, frame depth, channel count, and spatial size must match;
  do not use permissive loading to declare an incompatible checkpoint valid.
- If `TEST.OUTPUT_SAVE_DIR` is enabled, trainers hand predictions and labels to
  the shared saver. It writes a pickle containing `predictions`, `labels`,
  `label_type`, and `fs`; exact derived locations and metrics belong to the
  linked evaluation skill.

## Safe extension rule

To add a model, define a model class, implement the trainer contract and a loss,
add one exact dispatch branch to both paths in `main.py`, add config defaults,
and create train/inference templates. Preserve the input/output and checkpoint
contracts in [model-overview.md](references/model-overview.md). First run a
construction/forward smoke with synthetic tensors; do not run a dataset or
training loop as an extension test. Keep exploratory model tests, vendor
repositories, checkpoints, and source-checkout imports out of this runtime
skill.

PhysMamba is not a CPU fallback. Read [references/mamba-backend.md](references/mamba-backend.md)
before choosing it. For predictable failures, use
[references/troubleshooting.md](references/troubleshooting.md).
