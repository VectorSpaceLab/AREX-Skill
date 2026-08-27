# Training and Evaluation Workflows

## Purpose

Read this to build Torch Points3D train/eval commands, understand what `Trainer`
does, and choose safe smoke settings before launching expensive experiments.

## Hydra train command shape

`train.py` is decorated with `@hydra.main(config_path="conf", config_name="config")`.
It loads `conf/config.yaml`, relaxes OmegaConf struct mode, creates `Trainer(cfg)`,
and calls `trainer.train()`.

A complete command normally selects:

```bash
python train.py \
  task=<task> \
  models=<task>/<model-family> \
  data=<task>/<dataset-config> \
  model_name=<entry-under-model-config>
```

Example safe CPU/debug pattern:

```bash
python train.py \
  task=segmentation \
  models=segmentation/pointnet2 \
  data=segmentation/shapenet-fixed \
  model_name=pointnet2_charlesssg \
  training.cuda=-1 \
  training.num_workers=0 \
  training.wandb.log=False \
  training.tensorboard.log=False \
  training.tensorboard.pytorch_profiler.log=False \
  debugging=early_break
```

`debugging=early_break` limits training to an early break when the config group
is available. Still expect output-directory writes and dataset access.

## Eval command shape

`eval.py` is decorated with `@hydra.main(config_path="conf", config_name="eval")`.
It creates `Trainer(cfg)` and calls `trainer.eval()`.

```bash
python eval.py \
  checkpoint_dir=/path/to/run \
  model_name=<model-name> \
  weight_name=latest \
  cuda=-1 \
  batch_size=1 \
  num_workers=0
```

The eval config writes under `${checkpoint_dir}/eval/<timestamp>` by default.
Set `tracker_options.full_res` and `tracker_options.make_submission` only when
the dataset and task support those modes.

## What `Trainer` initializes

`Trainer(cfg)` coordinates:

1. Device choice: `cfg.training.cuda > -1` and `torch.cuda.is_available()` chooses CUDA; otherwise CPU.
2. W&B launch if `training.wandb.log` is true.
3. `ModelCheckpoint` using `training.checkpoint_dir`, `model_name`, and `training.weight_name`.
4. Dataset/model creation from checkpoint config when resuming, or from `cfg.data` and `cfg.models` for fresh training.
5. Optimizer setup, pretrained-weight setup, dataloader creation, model data verification, tracker selection, and visualizer setup.
6. Training epochs with tracker metrics, checkpoint saves, optional TensorBoard/profiler traces, and optional visualization output.

For smoke work, failures in any earlier stage usually mean a config/data/model
problem; do not move directly to long training.

## Common model/data combinations

| Task | Model config group | Example model_name | Data config examples | Notes |
| --- | --- | --- | --- | --- |
| Segmentation | `segmentation/pointnet2` | `pointnet2_charlesssg`, `pointnet2_largemsg` | `segmentation/shapenet-fixed`, `segmentation/s3disfused`, `segmentation/scannet` | Good first dense workflow. |
| Segmentation | `segmentation/rsconv` | `RSConv_MSN`, `RSConv_Indoor` | S3DIS/ShapeNet/ScanNet variants | Dense/message-style models. |
| Segmentation | `segmentation/kpconv` | `KPConvPaper` | S3DIS/ScanNet/ShapeNet variants | Partial-dense; may benefit from `precompute_multi_scale`. |
| Segmentation/panoptic | `segmentation/sparseconv3d`, `segmentation/minkowski_baseline`, `panoptic/pointgroup` | `ResUNet32`, `Res16UNet34`, `PointGroup` | sparse ScanNet/S3DIS variants | Requires sparse backends. |
| Object detection | `object_detection/votenet` or `votenet2` | `VoteNetPaper`, `VoteNetKPConv`, `VoteNetPN2` | `object_detection/scannet` variants | Box labels and VoteNet-specific properties. |
| Registration | `registration/kpconv`, `registration/pointnet2`, `registration/minkowski`, `registration/spconv3d` | `KPFCNN`, `pointnet2_charlesmsg`, `ResUnet32` | 3DMatch/KITTI/ModelNet/ETH/TUM variants | Use registration sub-skill for descriptor/evaluation details. |

## Logging and visualization controls

- `training.wandb.log`: set false for offline smoke runs.
- `training.tensorboard.log`: set false to avoid TensorBoard event writes.
- `training.tensorboard.pytorch_profiler.log`: set false unless profiling is the task.
- `visualization`: config group controls saved visual artifacts. Visualization can be I/O-heavy.

## Precompute multiscale

`Trainer.precompute_multi_scale` is true only when the model `conv_type` is
`PARTIAL_DENSE` and `training.precompute_multi_scale` is true. This is intended
for KPConv-style workflows; enabling it for other conv types can fail during
collation.

## Safe preflight order

1. Run the root environment probe.
2. Run `compose_config_smoke.py` for selected Hydra groups.
3. Validate dataset layout or use tiny fixtures.
4. Disable external logging/profiling.
5. Run a short early-break or native tiny fixture only after the skill/user task needs runtime proof.
