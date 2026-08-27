# Configuration and Checkpoints

## Purpose

Read this when a Torch Points3D Hydra command fails to compose, a checkpoint
cannot be loaded, or a run folder needs inspection or migration.

## Core Hydra selectors

`conf/config.yaml` combines these selectors:

```yaml
defaults:
  - task: ???
  - visualization: default
  - lr_scheduler: exponential
  - training: default
  - debugging: default
  - models: ???
  - data: ???
  - sota
model_name: ???
```

A train command must supply a compatible set:

| Selector | Example | Meaning |
| --- | --- | --- |
| `task` | `segmentation` | Task family; also used by dataset/model factories. |
| `models` | `segmentation/pointnet2` | YAML group under `conf/models/`. |
| `data` | `segmentation/shapenet-fixed` | YAML group under `conf/data/`. |
| `model_name` | `pointnet2_charlesssg` | Key inside the selected model YAML. |

If a model config contains multiple entries, `model_name` must match exactly.
Common segmentation entries include `pointnet2_charlesssg`, `pointnet2_largemsg`,
`KPConvPaper`, `RSConv_MSN`, `ResUNet32`, and `Res16UNet34`.

## Data/model factory alignment

`instantiate_model(config, dataset)` uses:

- `config.data.task`
- `config.model_name`
- `config.models.<model_name>.class`

It imports `torch_points3d.models.<task>.<module>` and finds the class. If the
error says the model name is not within available keys, inspect the selected
`models=<task>/<family>` group and choose a valid key. If class import fails,
check optional backend dependencies first.

`instantiate_dataset(dataset_config)` uses `dataset_config.task` and
`dataset_config.class`; see the datasets sub-skill for details.

## Training fields that affect runtime

`conf/training/default.yaml` provides:

- `epochs`, `batch_size`, `shuffle`, `num_workers`.
- `cuda`: `-1` forces CPU; non-negative values request CUDA if available.
- `precompute_multi_scale`: only effective/safe for `PARTIAL_DENSE` models.
- Optimizer/lr/bn scheduler configs.
- `weight_name`, `checkpoint_dir`, and `enable_cudnn`.
- `wandb` and `tensorboard` blocks, including PyTorch profiler settings.

For local smoke runs, override `num_workers=0`, `cuda=-1`, W&B false,
TensorBoard false, profiler false, and `debugging=early_break`.

## Evaluation fields

`conf/eval.yaml` includes:

- `checkpoint_dir`: run directory containing `<model_name>.pt`.
- `model_name`: checkpoint basename without `.pt`.
- `weight_name`: metric key such as `latest`, `miou`, or another saved metric token.
- `batch_size`, `num_workers`, `cuda`, `precompute_multi_scale`.
- `enable_dropout`, `voting_runs`, and `tracker_options`.
- Hydra output directory: `${checkpoint_dir}/eval/<timestamp>`.

## Checkpoint object structure

Torch Points3D checkpoints are `.pt` files containing fields such as:

- `models`: dictionary with `latest` and/or `best_<metric>` state dicts.
- `stats`: `train`, `test`, and `val` metric history lists.
- `optimizer` and `schedulers`.
- `dataset_properties` and `run_config`.
- Optional `model_props`.

`ModelCheckpoint(load_dir, check_name, selection_stage, run_config=..., resume=False, strict=False)` loads
`<load_dir>/<check_name>.pt`. In resume mode it copies the selected checkpoint
into the current working directory to avoid overwriting the original run.

## Weight selection

`weight_name` chooses `best_<weight_name>` if present; otherwise the checkpoint
tries `latest`. If neither exists, loading raises an error. Use `summarize_runs.py`
to inspect available metrics and checkpoint files before changing `weight_name`.

## Old OmegaConf checkpoint conversion

Older checkpoints can contain OmegaConf containers that are hard to load in
newer environments. Use the bundled converter only on a copy or with `--backup`:

```bash
python sub-skills/training-evaluation/scripts/convert_checkpoint_omegaconf.py \
  --input run/model.pt --output run/model-converted.pt --backup run/model-original.pt
```

The converter recursively replaces OmegaConf `DictConfig` and `ListConfig`
instances with plain Python containers and preserves excluded keys such as
`models` and `optimizer` by default.

## Output folder inspection

Hydra training runs usually produce dated output folders containing `.pt`
checkpoints, config copies, logs, TensorBoard files, visualizations, and metric
stats. Use the bundled summarizer for a safe read-only inventory; unlike the
original repository helper, it never deletes empty folders.
