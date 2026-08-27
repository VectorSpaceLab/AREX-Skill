# Preprocessing pipeline and safe command construction

This is a command contract, not an instruction to run generation in a Creator
or verification session. The repository has no example dataset, and the
provided scripts iterate large sequence sets and write outputs. Use placeholders
for user paths, quote them, run one sequence at a time after a layout check,
and retain the exact command in an experiment log.

## Order of operations

```text
raw SemanticKITTI/KITTI files
  ├─ label/label_preprocess.py  -> dataset/labels/<seq>/*_1_1.npy, *_1_2.npy
  └─ image_2 + calib + depth model
       image2depth.sh            -> MobileStereoNet depth/*.npy
       depth2lidar.sh            -> pseudo-LiDAR *.bin plus calib/poses
       lidar2voxel.sh            -> sequences_<model>_sweep10/*/voxels/*.pseudo
                                      (query proposals are a separate artifact)
```

Do not skip calibration or poses between depth and voxelization. Do not run
`lidar2voxel.sh` before pseudo-LiDAR `.bin` files exist. The stage-2 query
suffix files are not emitted by the checked-in voxelizer; use an approved
stage-1/QPN workflow or a supplied query artifact and match the configured
suffix.

## Ground-truth labels

The source command is:

```bash
python label/label_preprocess.py \
  --kitti_root=<SEMANTIC_KITTI_ROOT> \
  --kitti_preprocess_root=<PREPROCESS_ROOT>
```

The script expects `<SEMANTIC_KITTI_ROOT>/dataset/sequences/<seq>/voxels/`
with paired `.label` and `.invalid` files, processes sequences `00..10`, and
writes `<PREPROCESS_ROOT>/labels/<seq>/<frame>_1_1.npy` and
`<frame>_1_2.npy`. It uses the local `semantic-kitti.yaml` mapping and marks
invalid voxels as `255`. It creates output directories and skips an existing
output file, so treat it as a mutating command and review destination and
resume behavior first. `--help` is the only safe native check:

```bash
python label/label_preprocess.py --help
```

## Image to depth (optional MobileStereoNet)

`image2depth.sh` changes into the bundled preprocessing MobileStereoNet
subdirectory, invokes `prediction.py` with the sequence-specific baseline,
reads `image_2` through `filenames/<seq>.txt`, and saves depth maps. Its source
variables include `data_path`, a `mobilestereonet/depth` symlink, and a
checkpoint path. The checked-in loop covers `00..21`; the baseline differs for
some sequence ranges. Do not copy its empty `data_path` literally and do not
use an unverified checkpoint or filename list.

The preparation notes identify this as an optional, separate legacy environment
(Python 3.6, PyTorch 1.4.0, torchvision 0.5.0, CUDA 10.0). GPU, checkpoint,
image storage, and long runtime are unverified here. Route installation and
backend questions to `../environment-and-installation/`; there is no claimed
CPU substitute. A user choosing a different depth model must preserve the
same downstream frame IDs and calibration convention and must independently
validate depth quality.

Safe review pattern (does not execute the pipeline):

```bash
ROOT='<VOXFORMER_ROOT>'
DATA='<USER_OUTPUT_ROOT>'
SEQ='08'
printf '%q\n' "$ROOT/preprocess/image2depth.sh" "$DATA" "$SEQ"
# Review the printed paths, then execute only after explicit approval.
```

The actual shell script is an all-sequence loop and is not a dry-run helper.
Prefer an operator-authored one-sequence invocation of the underlying predictor
with the exact `--datapath`, `--testlist`, `--num_seq`, `--loadckpt`,
`--dataset kitti`, `--model`, and `--savepath` values after checking its
separate environment. Do not bundle or link third-party implementation files
or weights from this route.

## Depth to pseudo-LiDAR

From the preprocessing directory, the repository wrapper calls:

```bash
python utils/depth2lidar.py \
  --calib_dir ./kitti/dataset/sequences/<SEQ> \
  --depth_dir ./mobilestereonet/depth/sequences/<SEQ> \
  --save_dir ./mobilestereonet/lidar/sequences/<SEQ>
```

The utility accepts optional `--max_high` (default `80`), reads `.npy` depth
files except names containing `std`, projects image pixels through `P2` and
`Tr`, filters points with nonnegative Velodyne x and z below `max_high`, adds a
unit intensity column, and writes float32 four-column `.bin` scans. The wrapper
then copies `calib.txt` and `poses.txt` from its relative
`data_odometry_calib/sequences/<SEQ>` location. Review all three directories
before running: a missing calibration or an accidental output path can produce
plausible-looking but unusable files.

Do not run the wrapper merely to test imports. Check the layout first and
construct a one-sequence command with `--help` or a reviewed command preview.

## Pseudo-LiDAR to voxel / query input

From the preprocessing directory, the wrapper calls:

```bash
python utils/lidar2voxel.py \
  --dataset ./mobilestereonet/lidar/ \
  --output ./kitti/dataset \
  --num_seq <SEQ> \
  --sequence_length 10
```

The utility reads `./mobilestereonet/lidar/sequences/<SEQ>`, parses its
calibration and poses for sweeps longer than one, and writes packed `.pseudo`
files under `sequences_msnet3d_sweep10/<SEQ>/voxels/`. It uses the fixed map
shape and range documented in [semantic-kitti-layout.md](semantic-kitti-layout.md).
The wrapper loops over `00..21` and is not a dry run. It may use the compiled
`mapping` module; source rebuilding and Eigen/toolchain questions belong to
`../environment-and-installation/`.

`queries/` is not an output directory of this script. Stage 2 only discovers
files matching `*.query_iou5203_pre7712_rec6153` by default (or the selected
`query_tag`). Confirm those files separately before stage-2 execution.

## Safe execution rules

- Use absolute, user-approved paths in a reviewed command; quote every path and
  sequence value. Avoid shell interpolation of untrusted directory names.
- Run `validate_dataset_layout.py` first and use `--require-raw-voxels` when
  conversion is intended. Check free disk space and output ownership outside
  this read-only skill.
- Never replace a missing stage-2 query set with `.pseudo` files or a checkpoint.
- Never point `--output`, `data_path`, `--save_dir`, or a symlink at the source
  tree unless overwrite and recovery are explicit.
- Stop on a failed sequence rather than continuing an all-sequence loop. Record
  model, sequence, sweep length, query tag, calibration source, and output root.
- No command in this reference is run by the layout checker, and no download or
  data regeneration is part of verification.
