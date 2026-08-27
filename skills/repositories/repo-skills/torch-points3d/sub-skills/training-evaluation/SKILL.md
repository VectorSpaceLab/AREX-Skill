---
name: training-evaluation
description: "Use Torch Points3D Hydra training, evaluation, Trainer,
  checkpoints, forward inference, visualization, and experiment-output helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Torch Points3D Training and Evaluation

Use this sub-skill when the user asks to compose Torch Points3D `train.py` or
`eval.py` commands, debug `Trainer`, resume or evaluate checkpoints, inspect
`outputs/<date>/<time>` runs, configure W&B/TensorBoard/visualization, or run
forward inference on unlabeled data from a trained checkpoint.

## Read First

- Read [training/evaluation workflows](references/training-evaluation-workflows.md) for command patterns, safe CPU smoke options, and trainer behavior.
- Read [configuration and checkpoints](references/configuration-and-checkpoints.md) for Hydra selector rules, `ModelCheckpoint`, resume/eval fields, and output directory conventions.
- Read [forward inference](references/forward-inference.md) before adapting checkpoint-based inference for unlabeled point clouds.
- Read [training/evaluation troubleshooting](references/troubleshooting.md) for Hydra errors, dataset downloads, logging/profiler side effects, checkpoint mismatch, and old config conversion.
- Run [compose_config_smoke.py](scripts/compose_config_smoke.py) to validate selectors without training.
- Run [summarize_runs.py](scripts/summarize_runs.py) to list checkpoint metrics without deleting runs.
- Run [convert_checkpoint_omegaconf.py](scripts/convert_checkpoint_omegaconf.py) only when an old checkpoint stores OmegaConf containers that need conversion.
- Run [forward_preflight.py](scripts/forward_preflight.py) before a real forward-inference job.

## Main Workflows

### Compose a training command

Training is a Hydra script, not an installed console entry point. In a Torch
Points3D-style project containing `train.py` and `conf/`, specify the task,
model config group, data config group, and model entry:

```bash
python train.py \
  task=segmentation \
  models=segmentation/pointnet2 \
  data=segmentation/shapenet-fixed \
  model_name=pointnet2_charlesssg \
  training.wandb.log=False \
  training.tensorboard.log=False \
  training.tensorboard.pytorch_profiler.log=False \
  debugging=early_break
```

Use the config smoke script first if the user is unsure whether selectors match.
For real runs, remove `debugging=early_break` and configure data roots, logging,
CUDA, batch size, and output directories intentionally.

### Evaluate a checkpoint

`eval.py` uses `conf/eval.yaml`. The essential fields are `checkpoint_dir`,
`model_name`, `weight_name`, `batch_size`, `num_workers`, `cuda`,
`precompute_multi_scale`, and `tracker_options`.

```bash
python eval.py checkpoint_dir=/path/to/run model_name=pointnet2_charlesssg weight_name=latest cuda=-1
```

Set `cuda=-1` for CPU-only evaluation. Keep `tracker_options.make_submission`
and `full_res` explicit when evaluating datasets that support submissions or
full-resolution voting.

### Inspect output runs

```bash
python sub-skills/training-evaluation/scripts/summarize_runs.py --outputs-dir outputs --json
```

The bundled helper finds `.pt` checkpoints, reads their `stats` dict when
possible, and reports malformed/empty folders without deleting anything.

### Forward inference from a checkpoint

The repo forward workflow adapts a checkpoint's training data config to a
forward dataset class and writes `.npy` predictions. It needs a real checkpoint,
input data root, and output directory. Use the preflight helper before launching
the real job:

```bash
python sub-skills/training-evaluation/scripts/forward_preflight.py \
  --checkpoint-dir /path/to/run --model-name pointnet2_charlesssg \
  --input-path /path/to/unlabeled-data --output-path /path/to/predictions
```

Then see [forward inference](references/forward-inference.md) for the command
shape and caveats.

## Boundary Rules

- For standalone `PointNet2`/`KPConv`/`RSConv` forward APIs without a Hydra run, use [model-apis](../model-apis/SKILL.md).
- For data layout, transform, or dataset-class lookup problems, use [datasets-transforms](../datasets-transforms/SKILL.md).
- For registration descriptor evaluation or test-set protocols, use [registration-workflows](../registration-workflows/SKILL.md).

## Safety Checklist

- Do not run full training, cross-validation, W&B checkpoint downloads, or dataset downloads without user approval for runtime, network, data size, and writes.
- For smoke runs, disable W&B/TensorBoard/profiler and set `debugging=early_break`.
- Prefer `cuda=-1` for CPU checks; use GPU only after the dependency stack matches the target CUDA build.
- Treat skipped sparse/CUDA checks as optional limitations, not as passes.
