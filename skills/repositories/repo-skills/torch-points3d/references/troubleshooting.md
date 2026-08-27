# Cross-Cutting Troubleshooting

## Purpose

Read this when a Torch Points3D task fails before it reaches a workflow-specific
step. For model API, dataset/transform, training/evaluation, and registration
failures, also read the nearest sub-skill troubleshooting reference.

## Import fails while importing application APIs

**Symptoms**

- `ModuleNotFoundError: No module named 'google_drive_downloader'`
- TensorBoard/protobuf descriptor errors while importing trackers or trainer.
- `ModuleNotFoundError` for `torch_scatter`, `torch_sparse`, `torch_cluster`, `torch_points_kernels`, or `torch_geometric`.

**Likely causes**

Torch Points3D imports a broad legacy stack through losses, metrics, datasets,
and trackers. Even high-level application constructors may transitively import
PyG datasets, TensorBoard, W&B, and optional data packages.

**Recovery**

1. Run `python scripts/torch_points3d_env_probe.py --json --require-package --require-pyg`.
2. Ensure PyTorch and PyG extension wheels match exactly: PyTorch version, CPU/CUDA variant, Python ABI, and platform.
3. Install `googledrivedownloader==0.4` if PyG 1.7 imports fail through `torch_geometric.datasets.reddit2`.
4. Pin `protobuf<3.20` when TensorBoard 2.6-era imports fail.
5. Keep `numpy<1.20` with old Numba/Open3D pins unless you have validated a newer dependency stack.

## Sparse backend unavailable

**Symptoms**

- `Could not load Minkowski Engine, please check that it is installed correctly`.
- `ModuleNotFoundError: No module named 'MinkowskiEngine'`.
- `ModuleNotFoundError: No module named 'torchsparse'`.
- `SparseConv3d(..., backend='minkowski')` fails during model construction.

**Likely causes**

Sparse convolution support is optional. `SparseConv3d` can target `minkowski` or
`torchsparse`; `torch_points3d.applications.minkowski` requires
`MinkowskiEngine` at import time. CPU package imports do not verify these
backends.

**Recovery**

1. Decide whether the user's task genuinely needs sparse convolution. Dense `PointNet2` or `RSConv` and partial-dense `KPConv` workflows may avoid it.
2. If sparse convolution is required, install a backend compatible with the target PyTorch/CUDA compiler stack.
3. Set `SPARSE_BACKEND=minkowski` or `SPARSE_BACKEND=torchsparse` only after the chosen backend imports.
4. Re-run `python scripts/torch_points3d_env_probe.py --json --require-sparse-backend` and a sparse workflow smoke before claiming success.

## Hydra command or config composition fails

**Symptoms**

- `Missing mandatory value: task`, `model_name`, `models`, or `data`.
- `Error locating target`, model class not found, or dataset class not found.
- An override works in one command but not another.

**Likely causes**

Torch Points3D Hydra commands rely on four coordinated selectors:
`task`, `models`, `data`, and `model_name`. Dataset configs also need a `task`
and `class` value. Model configs contain multiple model entries; `model_name`
must match one of them.

**Recovery**

1. Use [training-evaluation configuration notes](../sub-skills/training-evaluation/references/configuration-and-checkpoints.md) to build the command.
2. Run `python sub-skills/training-evaluation/scripts/compose_config_smoke.py --task segmentation --models segmentation/pointnet2 --data segmentation/shapenet-fixed --model-name pointnet2_charlesssg` from a checkout that has `conf/`, or pass `--conf-dir` to an equivalent config tree.
3. If only the data config is failing, use [datasets-transforms](../sub-skills/datasets-transforms/SKILL.md) and its transform/config smoke helper.

## W&B, TensorBoard, profiler, or output directories surprise a smoke run

**Symptoms**

- A short train/eval smoke tries to contact W&B.
- TensorBoard/profiler writes event files or raises profiler errors.
- Hydra changes the working directory under `outputs/`.

**Recovery**

For local smoke commands, override logging/profiling explicitly:

```bash
training.wandb.log=False training.tensorboard.log=False \
training.tensorboard.pytorch_profiler.log=False debugging=early_break
```

Use a scratch output directory, and check [training-evaluation](../sub-skills/training-evaluation/SKILL.md) before running commands that create checkpoints.

## Dataset acquisition or layout blocks a workflow

**Symptoms**

- Dataset constructor starts a large download.
- ScanNet/S3DIS/KITTI/3DMatch files are missing.
- `FORWARD_CLASS` inference dataset cannot be resolved for unlabeled data.

**Recovery**

1. Do not start downloads until the user accepts dataset size, license, credentials, and destination.
2. Use [data layout notes](../sub-skills/datasets-transforms/references/data-layouts.md) and bundled layout checkers before training.
3. For checkpoint forward inference, run `python sub-skills/training-evaluation/scripts/forward_preflight.py ...` before the real forward command.

## Version skew after source edits

If working in a local checkout and source files changed after the package was
installed, reinstall the package or ensure the checkout is on `PYTHONPATH` for
inspection. Do not mix conclusions from an old installed wheel with new source
edits.
