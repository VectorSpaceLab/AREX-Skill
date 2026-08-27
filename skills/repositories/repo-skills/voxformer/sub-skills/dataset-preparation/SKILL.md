---
name: dataset-preparation
description: "Validate and safely prepare SemanticKITTI-derived files for
  VoxFormer stage 1 query proposals and stage 2 semantic occupancy, without
  downloading data or regenerating artifacts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Dataset preparation

Use this route for a user-owned SemanticKITTI/KITTI Odometry data root and its
VoxFormer-derived labels, pseudo voxels, and query proposals. The route is
read-only by default: inspect the layout first, then hand any explicitly
approved preprocessing command to the operator. It does **not** download
SemanticKITTI, run MobileStereoNet, regenerate labels, voxelize point clouds,
or bundle a real dataset.

## Operating route

1. Choose the stage and the exact artifact naming parameters. Stage 1 uses
   `depthmodel=msnet3d`, `nsweep=10`, `voxels/*.pseudo`, and `_1_2.npy`
   targets. Stage 2 uses the same default pseudo-voxel family plus
   `queries/*.<query_tag>` and `_1_1.npy` targets. The standard stage-2 query
   tag is `query_iou5203_pre7712_rec6153`; do not replace it with the literal
   documentation shorthand `.query` unless the selected config says so.
2. Run the read-only checker from the VoxFormer root:

   ```bash
   python skills/disco/voxformer/sub-skills/dataset-preparation/scripts/validate_dataset_layout.py --help
   python skills/disco/voxformer/sub-skills/dataset-preparation/scripts/validate_dataset_layout.py \
     --root <KITTI_ROOT> --stage both --sequence 08
   ```

   `<KITTI_ROOT>` is the directory whose child is `dataset/`; it is commonly
   referenced by the repository's `./kitti/` config path. The checker reports
   missing files, frame mismatches, calibration/pose syntax errors, and known
   packed-file sizes without writing under the supplied root. Use
   `--require-raw-voxels` when validating inputs for label conversion rather
   than only runtime-ready artifacts.
3. Read [semantic-kitti-layout.md](references/semantic-kitti-layout.md) for
   the stage-specific tree and shape contracts. Confirm that image frame IDs,
   pseudo/query frame IDs, and target frame IDs agree before training.
4. If artifacts are absent and regeneration is explicitly approved, follow
   [preprocessing-pipeline.md](references/preprocessing-pipeline.md) in order:
   labels (if needed), image-to-depth, depth-to-pseudo-LiDAR, then
   LiDAR-to-voxel. Construct one-sequence commands with quoted user paths and
   review them; never execute the all-sequence shell loops blindly. Query
   proposals are a separate stage-1 output and are not created by the
   repository's `lidar2voxel.py` script.
5. For failures, use [troubleshooting.md](references/troubleshooting.md).
   Route Python/CUDA/version installation and the optional MobileStereoNet
   environment to [environment-and-installation](../environment-and-installation/SKILL.md).
   Route config naming, voxel geometry, temporal camera choices, and stage
   semantics to [model-configuration](../model-configuration/SKILL.md). Route
   training, checkpoint, and evaluation commands to
   [training-and-evaluation](../training-and-evaluation/SKILL.md).

## Hard gates

- The runtime dataset classes read `dataset/sequences/<seq>/calib.txt`,
  `poses.txt`, and `image_2/<frame>.png`; stage 2 also reads poses to align
  optional temporal reference images. `image_3` is documented source data but
  is not read by these dataset classes.
- Stage 1 must have matching `.pseudo` files and `_1_2.npy` labels. Its target
  is loaded and reshaped to `(128, 128, 16)` and has two semantic states in
  the QPN dataset path (`empty`, `occupied`).
- Stage 2 must have matching query files with the configured suffix and `_1_1.npy`
  labels. Its full target is loaded as `(256, 256, 32)`, uses 20 SemanticKITTI
  classes plus `255` as the invalid/unknown marker, and uses a `0.2` metre
  voxel size with scene extent `[0, -25.6, -2]` to `[51.2, 25.6, 4.4]` in the
  checked-in configs.
- Packed `.pseudo` and query occupancy files are unpacked by the dataset code
  into `256*256*32` values; the checked-in voxelizer's packed output is
  therefore `262144` bytes when complete. A checker size warning/error is not
  proof that semantic contents are correct.
- No synthetic fixture, parser check, or import proves a real SemanticKITTI
  run. The repository has no example dataset or native data test suite.

## Bundled resources

- [references/semantic-kitti-layout.md](references/semantic-kitti-layout.md)
- [references/preprocessing-pipeline.md](references/preprocessing-pipeline.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/validate_dataset_layout.py](scripts/validate_dataset_layout.py)
