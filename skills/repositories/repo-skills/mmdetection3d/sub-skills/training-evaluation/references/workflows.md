# Training and testing command workflows

This reference distills MMDetection3D v1.4.0 train/test launch behavior into command-construction rules. Use it after a config and, for testing, a checkpoint have already been selected.

## Launcher selection

| Situation | Command family | Key resource inputs | Notes |
| --- | --- | --- | --- |
| Quick train/debug on one process | `python tools/train.py CONFIG ...` | optional `CUDA_VISIBLE_DEVICES`; optional `--work-dir` | CPU mode is experimental and usually unsuitable for point-cloud models. |
| Quick test/eval on one process | `python tools/test.py CONFIG CHECKPOINT ...` | optional `CUDA_VISIBLE_DEVICES`; optional `--work-dir` | Required for documented `--show`/`--show-dir` visualization debugging. |
| Single node, multiple GPUs | `./tools/dist_train.sh CONFIG GPUS ...` or `./tools/dist_test.sh CONFIG CHECKPOINT GPUS ...` | `GPUS`, optional `PORT`, `NNODES`, `NODE_RANK`, `MASTER_ADDR` | The shell launcher wraps `torch.distributed.launch` and passes `--launcher pytorch`. |
| Multiple machines without Slurm | same `dist_*` shell launchers on every node | identical `NNODES`, shared `MASTER_ADDR`, shared `PORT`, unique `NODE_RANK` | Slow networks can bottleneck; all nodes must see compatible config/data/checkpoint paths. |
| Slurm-managed train/test | `./tools/slurm_train.sh ...` or `./tools/slurm_test.sh ...` | `PARTITION`, `JOB_NAME`, `GPUS`, `GPUS_PER_NODE`, `CPUS_PER_TASK`, optional `SRUN_ARGS` | The shell launcher calls `srun` and passes `--launcher=slurm`. |

Prefer the bundled generator for reproducible templates:

```bash
python scripts/build_train_test_command.py --help
```

The generator renders shell text only. Copy and review the command in the target runtime; do not treat generation as execution.

## Training workflow

1. Confirm the config's dataset root and annotations already exist.
2. Pick a work directory. CLI `--work-dir` has highest priority; otherwise config `work_dir` is used; otherwise the default is `./work_dirs/<config-basename>`.
3. Decide optimization/runtime toggles:
   - `--amp`: switch `OptimWrapper` to `AmpOptimWrapper` with dynamic loss scaling. Do not use if the config has an incompatible optimizer wrapper.
   - `--sync_bn torch|mmcv`: convert BatchNorm layers to SyncBatchNorm/MMSyncBN. Use mainly for distributed training.
   - `--auto-scale-lr`: only valid when the config includes `auto_scale_lr.enable` and `auto_scale_lr.base_batch_size`.
   - `--resume`: no value means auto-resume latest checkpoint from work dir; a value points to a concrete checkpoint.
   - `--cfg-options KEY=VALUE ...`: merge nested config overrides after the file is loaded.
4. Select single-process, distributed, or Slurm launcher. For distributed commands, set a non-default port when several jobs share one machine.
5. Review the rendered command before launching; training is long-running and most point-cloud configurations need CUDA-capable compiled ops.

Example single-process render:

```bash
python scripts/build_train_test_command.py train \
  configs/pointpillars/example_kitti.py \
  --work-dir work_dirs/pp_kitti_debug \
  --amp \
  --auto-scale-lr \
  --cfg-option train_cfg.val_interval=2
```

Example distributed render for one job on four visible GPUs:

```bash
python scripts/build_train_test_command.py dist-train \
  configs/pointpillars/example_kitti.py \
  --gpus 4 \
  --cuda-visible-devices 0,1,2,3 \
  --port 29500 \
  --work-dir work_dirs/job_a
```

Example Slurm render:

```bash
python scripts/build_train_test_command.py slurm-train \
  configs/pointpillars/example_kitti.py \
  work_dirs/pp_kitti \
  --partition dev \
  --job-name pp_kitti \
  --gpus 8 \
  --gpus-per-node 8 \
  --cpus-per-task 5
```

## Testing and evaluation workflow

1. Confirm the checkpoint matches the config family and class/task definition.
2. Choose whether the run is metric evaluation, benchmark result formatting, visualization debugging, or TTA evaluation.
3. Put evaluator output keys in nested config overrides. See [evaluation.md](evaluation.md) for dataset-specific names such as `test_evaluator.pklfile_prefix`, `test_evaluator.jsonfile_prefix`, `test_evaluator.csv_savepath`, `test_evaluator.submission_prefix`, and `test_evaluator.result_prefix`.
4. For saved visualization, add `--show-dir` and a matching `--task` choice. Add `--show` only when interactive/silent plotting behavior is desired; saved outputs do not require a display.
5. For TTA, add `--tta` only when the config contains both `tta_model` and `tta_pipeline` and the model is a supported 3D segmentation workflow.
6. Select launcher. Multi-GPU testing uses the distributed shell launcher; Slurm testing uses the Slurm wrapper.

Example validation render with saved predictions in a work directory:

```bash
python scripts/build_train_test_command.py test \
  configs/votenet/example_scannet.py \
  work_dirs/votenet/latest.pth \
  --work-dir work_dirs/votenet_eval
```

Example headless visualization render for LiDAR detection:

```bash
python scripts/build_train_test_command.py test \
  configs/second/example_kitti.py \
  work_dirs/second/latest.pth \
  --show-dir work_dirs/second/show \
  --task lidar_det \
  --score-thr 0.25
```

Example distributed submission-format render:

```bash
python scripts/build_train_test_command.py dist-test \
  configs/pointpillars/example_nuscenes.py \
  work_dirs/pointpillars/latest.pth \
  --gpus 8 \
  --port 29501 \
  --cfg-option test_evaluator.jsonfile_prefix=work_dirs/pointpillars/results_nusc
```

## Port and multi-job patterns

The distributed launcher defaults to port `29500`. Two distributed jobs on one host must not share the same visible devices and port.

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 PORT=29500 ./tools/dist_train.sh CONFIG_A 4
CUDA_VISIBLE_DEVICES=4,5,6,7 PORT=29501 ./tools/dist_train.sh CONFIG_B 4
```

For Slurm jobs, prefer a nested cfg override rather than editing configs:

```bash
GPUS=4 ./tools/slurm_train.sh PARTITION JOB_NAME CONFIG WORK_DIR --cfg-options env_cfg.dist_cfg.port=29500
```

## When to refuse or reroute

- The user has no config: route to configuration/model-zoo guidance.
- The dataset root or info files are not prepared: route to data preparation.
- The user asks for a deployment server, TorchServe package, FLOPs, or log plot: route to serving/tools guidance.
- The user asks to inspect saved 3D boxes, point coordinates, or OBJ files independent of evaluation launch: route to structures/visualization guidance.
