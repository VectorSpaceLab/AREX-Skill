# Training Workflow

## Purpose

Use this reference to turn an intended TransFuser experiment into a validated single-GPU or distributed launch, understand what the loop writes, and resume without silently changing the model contract. Read `data-format.md` for sample layout and `api-reference.md` for model/configuration details.

## 1. Establish the runtime

The learned training path is CUDA-only. It creates `torch.device('cuda:<local-rank>')`, calls `torch.cuda.set_device`, moves the model and every batch to CUDA, and uses NCCL for distributed training. CPU can validate files and some preprocessing, but cannot substitute for the selected training backend.

Known compatible versions from live construction-time verification:

| Component | Verified value |
|---|---|
| Python | 3.7 |
| PyTorch | 1.12.1+cu113 |
| CUDA visibility | passed on NVIDIA A100 |
| mmcv | `mmcv-full` 1.6.0 |
| mmdet | 2.25.0 |
| mmsegmentation | 0.25.0 |
| mmcls | 0.25.0 |
| torch-scatter | 2.1.0 |
| timm | 0.6.7 |
| repository imports | `config`, `data`, `model`, and `train` passed |
| dependency consistency | `pip check` passed |

The OpenMMLab and `torch-scatter` packages are installed separately from the frozen `requirements.txt`. `mmcv-full` must match the PyTorch/CUDA ABI; plain `mmcv` is not an equivalent substitute because the model imports compiled operators.

Run a no-training probe when preparing an environment:

```bash
python <this-sub-skill>/scripts/validate_training_setup.py \
  --repo-root <transfuser-checkout> \
  --dataset-root <dataset-root> \
  --setting all \
  --backbone transFuser \
  --parallel-training 0 \
  --check-runtime
```

The model's image encoder is created with `pretrained=True`. Fresh construction may cause `timm` to retrieve image weights. Pre-populate an approved cache or allow the download explicitly; do not discover this network dependency inside an unattended training job.

## 2. Choose the split

`GlobalConfig(root_dir, setting)` recognizes three strings:

- `all`: every top-level scenario and every town group below it becomes training data. The first top-level entry is also assembled as `val_data`, but `train.py` deliberately skips validation whenever `setting == 'all'`.
- `02_05_withheld`: second-level directory names containing `Town02` or `Town05` become validation groups; all other names become training groups. The match is a case-sensitive substring test.
- `eval`: does not create `train_data` or `val_data`. It is valid for model/agent configuration that needs no dataset, but **cannot be passed to `train.py`** without failing when datasets are constructed.

Directory enumeration is not sorted in the source. Do not depend on the identity of the first entry under `all`; use `02_05_withheld` for the implemented held-out split, or modify the checkout deliberately and record the new split.

## 3. Validate the dataset

The loader expects `<dataset-root>/<scenario>/<town-group>/<route>/<modality>/...`, not a flat route directory. With default `seq_len=1` and `pred_len=4`, each eligible current frame requires its current RGB, top-down, depth, semantics, LiDAR, and measurement files plus five label files from the current frame through four future frames.

Run the bundled preflight before allocating a GPU:

```bash
python <this-sub-skill>/scripts/validate_training_setup.py \
  --dataset-root <dataset-root> \
  --setting 02_05_withheld \
  --backbone geometric_fusion \
  --parallel-training 0 \
  --max-routes 12
```

The helper validates a bounded number of routes by default. Use `--max-routes 0` only when a complete scan is acceptable. It never writes into the dataset. See `data-format.md` for filenames, JSON fields, dtypes, and shapes.

## 4. Select the model contract

Choose exactly one case-sensitive backbone:

- `transFuser`: multi-scale transformer fusion of image and LiDAR features; this is the default and the only backbone the CLI help explicitly claims for velocity input.
- `late_fusion`: independent image/LiDAR encoders followed by feature addition.
- `latentTF`: transformer fusion where the first two LiDAR channels are replaced with a normalized positional grid.
- `geometric_fusion`: projected image/BEV correspondences are required in every batch.

The defaults are `image_architecture=regnety_032`, `lidar_architecture=regnety_032`, `use_velocity=0`, `n_layer=4`, `use_target_point_image=1`, and `use_point_pillars=0`. A checkpoint is coupled to all of these choices as well as loss-head and config dimensions. Do not infer compatibility from the `.pth` filename.

PointPillars changes the LiDAR encoder input from the two-bin BEV histogram to a learned 32-channel 256×256 canvas. It also requires raw XYZI points, `num_points`, and a working matching `torch-scatter` binary. See `api-reference.md` before enabling it.

## 5. Launch single-GPU training

`--parallel_training` defaults to `1`, so a plain Python launch must override it:

```bash
cd <transfuser-checkout>/team_code_transfuser
CUDA_VISIBLE_DEVICES=0 python train.py \
  --id baseline \
  --root_dir <dataset-root> \
  --logdir <log-root> \
  --batch_size 10 \
  --setting all \
  --backbone transFuser \
  --parallel_training 0
```

The effective output directory is `<log-root>/baseline`, because the script appends `--id` to `--logdir`. Single-GPU mode fixes `rank=0`, `local_rank=0`, and `world_size=1`, uses `cuda:0` relative to `CUDA_VISIBLE_DEVICES`, a normal AdamW optimizer, zero data-loader workers, and pinned memory.

## 6. Launch DDP with torchrun

Do not run `python train.py --parallel_training 1`; the script immediately reads `RANK`, `LOCAL_RANK`, and `WORLD_SIZE`. Launch it with `torchrun`:

```bash
cd <transfuser-checkout>/team_code_transfuser
CUDA_VISIBLE_DEVICES=0,1 \
OMP_NUM_THREADS=16 \
OPENBLAS_NUM_THREADS=1 \
torchrun \
  --nnodes=1 \
  --nproc_per_node=2 \
  --max_restarts=0 \
  --rdzv_id=1234576890 \
  --rdzv_backend=c10d \
  train.py \
  --id ddp-run \
  --root_dir <dataset-root> \
  --logdir <log-root> \
  --batch_size 10 \
  --setting 02_05_withheld \
  --parallel_training 1
```

Operational rules:

- `--batch_size` is per process/GPU; effective batch size is `batch_size × world_size`.
- `CUDA_VISIBLE_DEVICES` must expose the same number of GPUs as `--nproc_per_node`.
- NCCL and an NVIDIA GPU are mandatory. The process-group timeout is 15 minutes.
- Each rank gets a `DistributedSampler`; the training sampler epoch is advanced each epoch. DDP loaders use eight workers per rank and pinned memory.
- Rank 0 alone creates the log directory, writes TensorBoard/`args.txt`, and saves checkpoints. Loss dictionaries and totals are gathered to rank 0 before logging.
- `--sync_batch_norm 1` converts batch normalization before wrapping with DDP. Use it only with distributed training.
- `--zero_redundancy_optimizer 1` uses `ZeroRedundancyOptimizer` with AdamW and consolidates its state on rank 0 before saving. It has no effect in single-GPU mode.

The source sets `CUDA_VISIBLE_DEVICES` again inside each worker after deriving `local_rank`. Treat the pre-launch device map as authoritative and verify rank/device assignment with the preflight and startup log.

## Complete CLI catalog

All boolean-like options are integer flags; use `0` or `1` rather than bare switches.

| Flag | Type | Default | Meaning and constraints |
|---|---:|---:|---|
| `--id` | str | `transfuser` | Experiment identifier appended to `logdir`. |
| `--epochs` | int | `41` | Upper bound used by `range(start_epoch, epochs)`. |
| `--lr` | float | `1e-4` | AdamW learning rate; also the initial value for manual reductions. |
| `--batch_size` | int | `12` | Per-GPU batch size. |
| `--logdir` | str | `log` | Parent log directory; actual run directory is `<logdir>/<id>`. |
| `--load_file` | str | `None` | Model checkpoint path. Resume also requires the derived optimizer path. |
| `--start_epoch` | int | `0` | Loop start and Engine counter seed; not read from checkpoint. |
| `--setting` | str | `all` | `all` or `02_05_withheld` for training. `eval` exists in config but is not trainable. |
| `--root_dir` | str | nonportable author-local path | Always pass an explicit dataset root. |
| `--schedule` | int | `1` | If `1`, applies manual 0.1 learning-rate reductions. |
| `--schedule_reduce_epoch_01` | int | `30` | First zero-based loop epoch at which LR is multiplied by 0.1. |
| `--schedule_reduce_epoch_02` | int | `40` | Second zero-based loop epoch at which LR is multiplied by 0.1. |
| `--backbone` | str | `transFuser` | Exact choice: `transFuser`, `late_fusion`, `latentTF`, or `geometric_fusion`. |
| `--image_architecture` | str | `regnety_032` | `timm` image encoder; compatibility depends on backbone internals. |
| `--lidar_architecture` | str | `regnety_032` | `timm` LiDAR encoder; compatibility depends on backbone internals. |
| `--use_velocity` | int | `0` | CLI help limits supported use to `transFuser`; validate alternatives before porting. |
| `--n_layer` | int | `4` | Transformer block count assigned to config. Relevant to transformer variants. |
| `--wp_only` | int | `0` | If `1`, only `loss_wp` has nonzero aggregation weight. |
| `--use_target_point_image` | int | `1` | If `1`, concatenates a 1×256×256 target-point channel to LiDAR input. |
| `--use_point_pillars` | int | `0` | If `1`, encode padded raw points with PointPillars instead of histogram input. |
| `--parallel_training` | int | `1` | `1` requires `torchrun`; `0` is the plain single-GPU path. |
| `--val_every` | int | `5` | Validation frequency when setting is not `all`. The first loop epoch has index 0, so validation occurs after the first trained epoch. |
| `--no_bev_loss` | int | `0` | If `1`, changes the aggregate weight of `loss_bev` to zero. |
| `--sync_batch_norm` | int | `0` | Convert to SyncBatchNorm; only meaningful with DDP. |
| `--zero_redundancy_optimizer` | int | `0` | Use distributed optimizer-state sharding; only meaningful with DDP. |
| `--use_disk_cache` | int | `0` | Cache decoded data with a 768-GiB size limit. DDP expects `SCRATCH/dataset_cache`. |

`GlobalConfig.lr` exists but `train.py` constructs the optimizer from CLI `args.lr`. Similarly, the CLI overwrites `backbone`, `n_layer`, `use_target_point_image`, `use_point_pillars`, and optionally the BEV loss weight after constructing the config.

## Losses and validation

The model returns these keys in a fixed configured order:

| Loss | Default aggregation weight | Notes |
|---|---:|---|
| `loss_wp` | 1.0 | Mean absolute error over four ego waypoints. |
| `loss_bev` | 1.0 | Weighted 3-class BEV cross-entropy; `--no_bev_loss 1` sets this aggregate weight to zero. |
| `loss_depth` | 1.0 | L1 depth loss already multiplied inside the model by `ls_depth=10.0`. |
| `loss_semantic` | 1.0 | Semantic cross-entropy multiplied inside the model by `ls_seg=1.0`. |
| `loss_center_heatmap` | 0.2 | CenterNet Gaussian focal loss. |
| `loss_wh` | 0.2 | Box width/height L1. |
| `loss_offset` | 0.2 | Center offset L1. |
| `loss_yaw_class` | 0.2 | 12-bin yaw classification. |
| `loss_yaw_res` | 0.2 | Yaw residual SmoothL1. |
| `loss_velocity` | 0.0 | Computed and logged but excluded from the default total. |
| `loss_brake` | 0.0 | Computed and logged but excluded from the default total. |

`--wp_only 1` replaces all aggregate weights with `[1, 0, ..., 0]`; heads still run and return losses. The engine averages by number of batches and, under DDP, then averages rank-level values. Empty datasets therefore fail rather than producing a meaningful zero loss.

Validation runs only when `setting != 'all'` and the zero-based loop epoch is divisible by `val_every`. The validation sampler is configured with `shuffle=True`, so it is not a stable ordering guarantee.

## Logs, checkpoints, and resume

Rank 0 writes:

```text
<logdir>/<id>/
  args.txt                    # JSON serialization of all CLI arguments
  events.out.tfevents...      # TensorBoard scalars
  model_<engine-epoch>.pth    # model.state_dict()
  optimizer_<engine-epoch>.pth
  visualizations/             # only when config.debug is enabled
```

The Engine counter is incremented inside `train()`, so a run starting at `start_epoch=0` first saves `model_1.pth`. Learning-rate reduction checks use the outer zero-based loop value before that increment.

Resume example:

```bash
cd <transfuser-checkout>/team_code_transfuser
CUDA_VISIBLE_DEVICES=0 python train.py \
  --id resumed \
  --root_dir <dataset-root> \
  --logdir <log-root> \
  --load_file <old-run>/model_20.pth \
  --start_epoch 20 \
  --backbone transFuser \
  --image_architecture regnety_032 \
  --lidar_architecture regnety_032 \
  --parallel_training 0
```

The optimizer checkpoint is derived by replacing `model_` with `optimizer_` in the supplied path. There is no graceful fallback if it is missing. Scheduler state is not separately serialized; reductions are reproduced from `start_epoch` and the configured reduction epochs. Always copy the old `args.txt` into the compatibility review and deliberately preserve or override every architecture-affecting field.

DDP saves `self.model.state_dict()` on the wrapper for backward compatibility, so keys commonly carry a `module.` prefix. Single-GPU state dicts do not. Resume in the same mode is safest. If conversion is necessary, inspect keys first and perform an explicit, reviewed prefix transformation rather than loading with `strict=False` and ignoring missing keys.

Default-safe inspection:

```bash
python <this-sub-skill>/scripts/inspect_checkpoint.py <run>/model_20.pth \
  --args-file <run>/args.txt
```

This reports container metadata without unpickling. For a trusted checkpoint only, add `--unsafe-load` to inspect state-dict keys and tensor shapes on CPU.

## Cache and debug behavior

- With `--use_disk_cache 1`, labels are cached by label path; image/depth/semantic data are PNG-compressed in memory and BEV arrays use compressed NumPy storage.
- DDP cache mode uses `SCRATCH/dataset_cache` and gives `diskcache.Cache` a 768-GiB size limit. Confirm `SCRATCH`, free space, permissions, and per-node sharing before launch. The size limit is a cap, not a storage reservation.
- Single-GPU cache mode lets `diskcache` choose its default directory. Prefer an explicit maintained code change if storage location matters.
- The source cache encoding assumes multitask depth and semantics exist. Do not combine `multitask=False` with disk cache without first fixing and testing the `None` encoding path.
- Debug visualization is configured in `GlobalConfig`, not by a CLI flag. With `debug=True`, the Engine creates `<logdir>/<id>/visualizations` and model visualization runs every `train_debug_save_freq=50` forwards.
- Debug visualization assumes multitask outputs. It is also not rank-isolated, so enabling it unchanged under DDP can produce path contention. Prefer single-GPU debug or add a deliberate rank-specific output policy.

## Stop conditions

Do not launch when any of these remains unresolved:

- CUDA is absent or the PyTorch/CUDA/compiled-extension ABI does not match;
- the dataset validator reports missing modalities, future labels, empty split sides, or no eligible frames;
- a requested architecture cannot expose the stages expected by the selected backbone;
- DDP rank variables are absent or world size disagrees with visible devices;
- a resume pair, trusted provenance, or exact model contract is missing;
- required pretrained image weights are neither cached nor approved for retrieval;
- available storage cannot accommodate checkpoints, events, debug images, or cache growth.
