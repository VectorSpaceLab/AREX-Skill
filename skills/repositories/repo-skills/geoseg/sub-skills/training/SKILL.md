---
name: training
description: "Run or adapt GeoSeg supervised PyTorch Lightning training from a
  Python config, including loaders, augmentation, losses, optimization,
  checkpoints, resumption, and metric interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# GeoSeg training

Use this sub-skill when a downstream agent must start, adapt, or diagnose a
supervised GeoSeg training run. The native entrypoint is `train_supervision.py`,
but invoke it through the shared bundled wrapper below; do not launch checkout
files directly. It accepts a Python config rather than command-line
hyperparameter overrides. Full training is **skip-expensive** and
**data/checkpoint dependent**: do not launch it unless the requested dataset
layout, model/backbone weights, output locations, GPU budget, and stopping
criterion are all available.

## Route first

- Use [workflows.md](references/workflows.md) for the preflight, config,
  checkpoint, and metric lifecycle.
- Use [cli-reference.md](references/cli-reference.md) for exact flags, config
  fields, dataset layouts, and command templates.
- Use [troubleshooting.md](references/troubleshooting.md) for dependency,
  data/config, CLI, backend, checkpoint, and workflow failures.
- Route dataset conversion, patch splitting, and mask preparation to the
  `data-preparation` sub-skill. Route model selection and config construction
  to `model-and-config`. Route testing, checkpoint evaluation, and inference
  output rendering to `evaluation-inference`.

Do not implement preprocessing or inference rendering here.

## Safe entry point

Before importing a config, run the bundled static validator. It parses Python
syntax and assignment names without executing imports, constructing datasets or
models, downloading weights, or launching training:

Set `GEOSEG_SKILL` to the generated skill directory and use absolute config
paths when diagnosing from an arbitrary working directory:

```bash
export GEOSEG_SKILL=/path/to/this/skill
python "$GEOSEG_SKILL/sub-skills/training/scripts/check_training_config.py" \
  /path/to/GeoSeg/config/<dataset>/<model>.py
```

For native training, use the shared bundled wrapper rather than invoking the
checkout entrypoint directly. Replace `/path/to/GeoSeg` with the user's GeoSeg
checkout; `--repo-root` must point to that checkout. The config path remains a
user-provided argument and is passed unchanged to the native CLI:

```bash
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root /path/to/GeoSeg \
  train_supervision.py -c config/<dataset>/<model>.py
```

`-c` and `--config_path` are equivalent and required. There is no native
`--epochs`, `--batch-size`, `--resume`, or GPU override flag; make those
changes in a copied config and validate it again. The native `--help` smoke
check is a lightweight integration check, not evidence that a full run is
possible:

```bash
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root /path/to/GeoSeg \
  train_supervision.py --help
```

Run that smoke check only after this generated skill is integrated with the
repository environment. Never use `--help` as a substitute for dataset or
checkpoint validation.

## Operating rules

1. Validate the config statically, then verify its referenced data and weight
   paths before allowing Python config import. LoveDA creates
   `loveda_val_dataset` at module import, so even a config inspection that
   imports `geoseg.datasets.loveda_dataset` requires the external LoveDA Val
   tree. The static validator intentionally avoids this side effect.
2. Ensure the config's `num_classes`, `classes`, `ignore_index`, model output,
   and loss agree. A loader batch must contain `img` and
   `gt_semantic_seg`; masks must be integer class labels with the configured
   ignore value.
3. Select exactly one checkpoint intent: `pretrained_ckpt_path` initializes a
   `Supervision_Train` model from a checkpoint, while `resume_ckpt_path` asks
   Lightning to restore a training state during `trainer.fit`. Do not combine
   them accidentally; see [workflows.md](references/workflows.md).
4. Ensure `monitor` is one of the metrics actually logged by the script and
   that `monitor_mode` matches the desired direction before creating
   `ModelCheckpoint`.
5. Treat `gpus='auto'` as a Lightning device selection request, not a promise
   of a GPU. Confirm accelerator visibility and effective device count. Start
   with a deliberately small batch/crop smoke run only when data and weights
   are real; otherwise stop after static validation.
6. Report train and validation `mIoU`, `F1`, and `OA`, plus per-class IoU.
   Interpret mIoU/F1 with the dataset-specific last-class exclusion described
   in [cli-reference.md](references/cli-reference.md), rather than silently
   comparing incompatible averages.
7. Record the config path, commit/version, effective data roots, checkpoint
   intent, monitor, device setting, seed caveat, and whether training was
   skipped as expensive. Do not claim a result from a config-only or
   `--help` check.

## Known implementation caveats

The source imports `pytorch_lightning`, not the `lightning` namespace. The
requirements list both `lightning==2.0.0` and `pytorch-lightning==2.3.0`, but
the verified inspection environment used `pytorch-lightning==2.3.0` and omitted
the conflicting/unused `lightning` meta-package. Keep the source import and
prefer the verified package set; do not “fix” this by changing imports during a
training run.

`seed_everything(42)` is hard-coded in `main`; it seeds Python, NumPy, Torch,
and CUDA, sets cuDNN deterministic mode, and then also sets
`torch.backends.cudnn.benchmark=True`. Expect residual nondeterminism and
record hardware/backend details. `accumulate_n` appears in one config but is
not consumed by `train_supervision.py`, so it does not provide gradient
accumulation without a code change.

PyramidMamba's optional `mamba_ssm` dependency is unverified in this checkout;
route that model through dependency troubleshooting and do not mark it
training-ready based only on the config validator.
