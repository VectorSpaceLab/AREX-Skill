# Training and evaluation troubleshooting

Use this when a generated command fails to parse, hangs at launch, produces no expected results, or hits MMEngine/MMDetection3D runtime assertions.

## Command and config override failures

### `--cfg-options` did not affect the evaluator

Likely cause: the override was passed as a top-level key. Evaluator settings normally live under `test_evaluator`.

Prefer:

```bash
--cfg-options test_evaluator.pklfile_prefix=work_dirs/eval/results
```

Avoid unless the config explicitly consumes it:

```bash
--cfg-options submission_prefix=work_dirs/eval/submission
```

### Lists, tuples, or strings fail to parse

`--cfg-options` uses MMEngine's dictionary action. Keep each override as `KEY=VALUE`, avoid spaces around `=`, and quote shell-sensitive values:

```bash
--cfg-options 'model.test_cfg.nms_thr=0.01' 'train_cfg.val_interval=2'
```

For lists/tuples, quote the whole token so the shell does not split it.

## Training-specific failures

### AMP assertion

`--amp` only rewrites configs whose `optim_wrapper.type` is `OptimWrapper`. If the config already uses `AmpOptimWrapper`, training warns that AMP is already enabled. If it uses another wrapper, remove `--amp` or update the config deliberately.

### Auto-scale LR runtime error

`--auto-scale-lr` requires all of these keys in the config:

- `auto_scale_lr`
- `auto_scale_lr.enable`
- `auto_scale_lr.base_batch_size`

If any are missing, either add them through config customization or manually tune optimizer learning rate with a `--cfg-options` override.

### Resume did not load the checkpoint expected

- `--resume` with no value means auto-resume from the latest checkpoint in `work_dir`.
- `--resume some/path.pth` means resume from that exact checkpoint and sets `load_from` accordingly.
- `--work-dir` changes where auto-resume searches, so keep resumed commands consistent with the original work directory.

### SyncBN problems

`--sync_bn torch|mmcv` converts BatchNorm layers for synchronized distributed statistics. It is not a cure for CPU execution, bad checkpoints, or mismatched GPU counts. If a model has no suitable BatchNorm layers or the backend does not support the selected SyncBN implementation, remove the flag.

## Test/evaluation-specific failures

### Visualization hook assertion asks for `--task`

Whenever `--show` or `--show-dir` is present, pass exactly one valid task:

```bash
--task lidar_det
```

Choices are `mono_det`, `multi-view_det`, `lidar_det`, `lidar_seg`, and `multi-modality_det`.

### Visualization hook is missing from config

Custom configs may have removed `default_hooks.visualization`. Add or inherit the default 3D visualization hook in the config, or remove `--show`/`--show-dir` if visualization is not required.

### Saved visualization has no GUI

Saved outputs through `--show-dir` do not require a display. If interactive display is failing on a remote server, omit `--show` and keep `--show-dir --task ...`.

### `--tta` assertion about `tta_model` or `tta_pipeline`

The selected config does not define segmentation TTA. Remove `--tta`, switch to a supported segmentation config, or add the missing TTA sections through config customization. Do not use `--tta` as a generic detection option in this release.

### No result/submission files were saved

Check the evaluator type and required output key:

- KITTI detection: `test_evaluator.pklfile_prefix` for pickle results and `test_evaluator.submission_prefix` for text submissions.
- nuScenes: `test_evaluator.jsonfile_prefix`.
- Lyft: `test_evaluator.jsonfile_prefix` plus `test_evaluator.csv_savepath` when CSV is needed.
- Waymo v1.4.0 metric: `test_evaluator.result_prefix`; the config also needs a valid `waymo_bin_file`.
- Segmentation: `test_evaluator.submission_prefix` for benchmark submissions where supported.

For official test-set submissions, also confirm the dataset `ann_file` and `data_prefix` point to the test split, not validation.

## Distributed launch failures

### Job hangs or reports address/port already in use

The distributed shell launchers default to port `29500`. Give every simultaneous distributed job a unique port:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 PORT=29500 ./tools/dist_train.sh CONFIG_A 4
CUDA_VISIBLE_DEVICES=4,5,6,7 PORT=29501 ./tools/dist_train.sh CONFIG_B 4
```

For Slurm, prefer passing the port as a nested config override:

```bash
GPUS=4 ./tools/slurm_train.sh PARTITION JOB CONFIG WORK_DIR --cfg-options env_cfg.dist_cfg.port=29500
```

### GPU count mismatch

`GPUS`/`--nproc_per_node` must match the number of visible devices intended for the job. If `CUDA_VISIBLE_DEVICES=0,1,2,3`, use `GPUS=4`, not the host's full GPU count.

### Multi-node jobs fail to rendezvous

Every node must agree on:

- `NNODES`
- `MASTER_ADDR`
- `PORT`
- identical config/data/checkpoint visibility

Each node must use a unique `NODE_RANK` from `0` to `NNODES-1`.

## Slurm failures

### Resources do not match allocation

The Slurm wrappers use these environment variables:

- `GPUS` total tasks/GPU processes, default `8`.
- `GPUS_PER_NODE`, default `8`.
- `CPUS_PER_TASK`, default `5`.
- `SRUN_ARGS` for site-specific `srun` arguments.

If the cluster grants fewer GPUs per node than the command asks for, lower `GPUS_PER_NODE` and total `GPUS` or request a larger allocation.

### Command works outside Slurm but not inside Slurm

Check that the Slurm job environment activates the same Python package stack, sees the same dataset/checkpoint paths, and exports any needed storage variables. The generated runtime command intentionally does not encode local environment paths.

## CPU/GPU/backend failures

### CPU training/testing fails for point-cloud models

This is expected for many LiDAR pipelines because they depend on CUDA 3D operations or sparse backends. CPU operation is documented as experimental and narrow; SMOKE/monocular debugging is the safer CPU path.

### CUDA extension or sparse backend import error

Do not treat command syntax as wrong until the package/backend environment is verified. Check the installed PyTorch/CUDA/MMCV/MMSeg/MMDet/MMDetection3D stack and any model-specific sparse dependency required by the config.

### KITTI metric GPU skip/error

Some KITTI metric paths rely on CUDA-backed rotated IoU behavior in the test suite. If CUDA is unavailable, use command/static verification and record that full KITTI metric validation is backend-blocked.

## Safe recovery procedure

1. Re-render the intended command with `scripts/build_train_test_command.py` to remove shell quoting mistakes.
2. Check the config/evaluator fields before launching.
3. For distributed jobs, check visible GPUs and unique port.
4. For visualization/TTA, check the required config hooks/keys.
5. Only after syntax/config/backend checks are clean should an expensive train/test run be retried.
