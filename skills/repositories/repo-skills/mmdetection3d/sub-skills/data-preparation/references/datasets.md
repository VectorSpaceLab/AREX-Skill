# Built-in Dataset Preparation Reference

This reference distills the MMDetection3D v1.4.0 dataset-preparation guides and converter dispatch code into self-contained operating notes. Use it with the safe helpers in [`../scripts/`](../scripts/). The helpers do not download or convert data; they only check path layouts or render commands to review.

## Stage vocabulary used by this sub-skill

- `source`: files as acquired from the official dataset or the dataset's auxiliary export scripts before MMDetection3D's `create_data.py` conversion.
- `preconvert`: the layout expected immediately before running the native `create_data.py` dispatcher. For outdoor datasets this is usually the same as `source`; for indoor/RGB-D datasets it is after the dataset-provided export or MATLAB extraction step.
- `converted`: files expected after `create_data.py` completes.

When the user's config uses a non-standard root, the same directory names can be preserved under that root, then `data_root`, `data_prefix`, and `ann_file` must be changed in the config.

## Native conversion dispatcher

The v1.4.0 converter dispatcher accepts these dataset names:

| Dataset argument | Default version/tag | Important options | Notes |
| --- | --- | --- | --- |
| `kitti` | tag `kitti` | `--with-plane`, `--only-gt-database` | Generates reduced point clouds, v2 info pickles, and ground-truth database. |
| `waymo` | `--version v1.4`, tag `waymo` | `--workers`, `--max-sweeps`, `--only-gt-database`, `--skip-saving-sensor-data`, `--skip-cam_instances-infos` | Converts TFRecords into KITTI-style data under `kitti_format/`; requires Waymo/TensorFlow tooling. |
| `nuscenes` | `--version v1.0`, tag `nuscenes` | `--max-sweeps`, `--only-gt-database` | Full version creates train/val/test infos; `v1.0-mini` creates mini train/val infos. |
| `lyft` | `--version v1.01`, tag `lyft` | `--max-sweeps` | Run the Lyft data fixer after conversion for the known corrupted lidar file. |
| `semantickitti` | tag `semantickitti` | none specific | Generates train/val/test segmentation info pickles. |
| `s3dis` | tag `s3dis` | `--workers` | Requires S3DIS export output before conversion. |
| `scannet` | tag `scannet` | `--workers` | Requires ScanNet export output before conversion. |
| `sunrgbd` | tag `sunrgbd` | `--workers` | Requires MATLAB-extracted SUN RGB-D files before conversion. |

Important version-specific caution: the v1.4.0 documentation describes a `custom` create-data command, but the inspected v1.4.0 `create_data.py` dispatcher does not contain a `custom` branch. Treat custom data as a schema/config task; do not promise a verified built-in `create_data.py custom` conversion without adding or supplying a converter. See [`custom-dataset.md`](custom-dataset.md).

Render commands with the bundled helper, then review before running:

```bash
python ../scripts/build_create_data_command.py create-data kitti --root-path data/kitti --out-dir data/kitti --extra-tag kitti
python ../scripts/build_create_data_command.py update-infos --dataset kitti --pkl-path data/kitti/kitti_infos_trainval.pkl --out-dir data/kitti_v2_infos
```

## KITTI

### Preconvert layout

```text
kitti/
├── ImageSets/
│   ├── train.txt
│   ├── val.txt
│   ├── trainval.txt
│   └── test.txt
├── training/
│   ├── calib/
│   ├── image_2/
│   ├── label_2/
│   ├── velodyne/
│   └── planes/        # optional road planes for plane-aware augmentation
└── testing/
    ├── calib/
    ├── image_2/
    └── velodyne/
```

### Command family

```bash
python ../scripts/build_create_data_command.py create-data kitti --root-path data/kitti --out-dir data/kitti --extra-tag kitti
python ../scripts/build_create_data_command.py create-data kitti --root-path data/kitti --out-dir data/kitti --extra-tag kitti --with-plane
python ../scripts/build_create_data_command.py create-data kitti --root-path data/kitti --out-dir data/kitti --extra-tag kitti --only-gt-database
```

Use `--with-plane` only when `training/planes/` exists. Use `--only-gt-database` when ready-made info pickles were placed under the root but `ObjectSample` augmentation still needs `kitti_gt_database/` and `kitti_dbinfos_train.pkl`.

### Converted outputs

Expected core outputs include `kitti_infos_train.pkl`, `kitti_infos_val.pkl`, `kitti_infos_trainval.pkl`, `kitti_infos_test.pkl`, `training/velodyne_reduced/`, `testing/velodyne_reduced/`, `kitti_gt_database/`, and `kitti_dbinfos_train.pkl`.

Info files use the v2 structure with `metainfo` and `data_list`. For each sample, typical keys include camera metadata under `images`, point-cloud metadata under `lidar_points`, optional `plane`, and object annotations under `instances`.

## Waymo

### Preconvert layout

```text
waymo/
├── waymo_format/
│   ├── training/       # TFRecord segments
│   ├── validation/     # TFRecord segments
│   ├── testing/        # TFRecord segments
│   ├── gt.bin          # validation ground truth for evaluation
│   ├── cam_gt.bin      # optional camera-only ground truth
│   └── fov_gt.bin      # optional FOV ground truth
└── kitti_format/
    └── ImageSets/      # split txt files or destination for generated split files
```

### Command family

```bash
python ../scripts/build_create_data_command.py create-data waymo --root-path data/waymo --out-dir data/waymo --extra-tag waymo --version v1.4 --workers 128 --quiet-tf
python ../scripts/build_create_data_command.py create-data waymo --root-path data/waymo --out-dir data/waymo --extra-tag waymo --version v1.4-mini --workers 8 --quiet-tf
python ../scripts/build_create_data_command.py create-data waymo --root-path data/waymo --out-dir /large_disk/waymo_out --extra-tag waymo --version v1.4 --workers 32 --skip-cam_instances-infos
```

`--quiet-tf` renders `TF_CPP_MIN_LOG_LEVEL=3` before the command. If conversion is slow, blocked, or exhausting memory, reduce `--workers`; use `--workers 0` to avoid multiprocessing when diagnosing a hang. If `--out-dir` is not the dataset root, link or copy the resulting `kitti_format/` back to the location expected by configs.

### Converted outputs

`create_data.py waymo` writes to `<out-dir>/kitti_format/`. Expected outputs include:

```text
kitti_format/
├── ImageSets/{train,val,trainval,test}.txt
├── training/{image_0,image_1,image_2,image_3,image_4,velodyne}/
├── testing/{image_0,image_1,image_2,image_3,image_4,velodyne}/
├── waymo_gt_database/
├── waymo_infos_train.pkl
├── waymo_infos_val.pkl
├── waymo_infos_trainval.pkl
├── waymo_infos_test.pkl
└── waymo_dbinfos_train.pkl
```

For `v1.4-mini`, expect only training and validation conversions. Waymo info entries include ego/global transforms, timestamps, context names, lidar/image sweeps, camera matrices, ordinary instances, camera-synchronous instances, and per-camera instances.

## NuScenes

### Preconvert layout

```text
nuscenes/
├── maps/
├── samples/
├── sweeps/
├── lidarseg/          # optional, for lidar segmentation annotations
├── v1.0-trainval/
└── v1.0-test/
```

For `v1.0-mini`, use the mini metadata folder instead of the full trainval/test metadata.

### Command family

```bash
python ../scripts/build_create_data_command.py create-data nuscenes --root-path data/nuscenes --out-dir data/nuscenes --extra-tag nuscenes --version v1.0 --max-sweeps 10
python ../scripts/build_create_data_command.py create-data nuscenes --root-path data/nuscenes --out-dir data/nuscenes --extra-tag nuscenes --version v1.0-mini --max-sweeps 10
python ../scripts/build_create_data_command.py create-data nuscenes --root-path data/nuscenes --out-dir data/nuscenes --extra-tag nuscenes --only-gt-database
```

Use `--only-gt-database` when info pickles already exist but object sampling still needs `nuscenes_database/` and `nuscenes_dbinfos_train.pkl`.

### Converted outputs

Full conversion expects `nuscenes_infos_train.pkl`, `nuscenes_infos_val.pkl`, `nuscenes_infos_test.pkl`, `nuscenes_database/`, and `nuscenes_dbinfos_train.pkl`. Mini conversion normally has train/val info files only.

Info files contain lidar sweeps, six camera records, ego/global transforms, instances, optional per-camera instances, and optional `pts_semantic_mask_path` when lidarseg is prepared. Remember that LiDAR and camera boxes use different dimension/yaw conventions; route geometry debugging to `structures-visualization`.

## Lyft

### Preconvert layout

```text
lyft/
├── v1.01-train/
│   ├── v1.01-train/
│   ├── lidar/
│   ├── images/
│   └── maps/
├── v1.01-test/
│   ├── v1.01-test/
│   ├── lidar/
│   ├── images/
│   └── maps/
├── train.txt
├── val.txt
├── test.txt
└── sample_submission.csv
```

Lyft does not provide an official train/val split; MMDetection3D uses provided split text files. Keep the original folder names as above.

### Command family

```bash
python ../scripts/build_create_data_command.py create-data lyft --root-path data/lyft --out-dir data/lyft --extra-tag lyft --version v1.01 --include-lyft-fixer
```

The helper renders both the `create_data.py lyft` command and the post-conversion Lyft data-fixer command when `--include-lyft-fixer` is set.

### Converted outputs

Expected outputs are `lyft_infos_train.pkl`, `lyft_infos_val.pkl`, and `lyft_infos_test.pkl`. Unlike NuScenes, Lyft v1.4.0 guidance does not rely on a generated ground-truth database for routine training.

## SemanticKITTI

### Preconvert layout

```text
semantickitti/
└── sequences/
    ├── 00/
    │   ├── velodyne/
    │   └── labels/
    ├── 01/
    ├── ...
    └── 22/
```

Sequences 00-07 and 09-10 are training, sequence 08 is validation, and 11-22 are test. Label files encode instance ids in the high 16 bits and semantic ids in the low 16 bits.

### Command family

```bash
python ../scripts/build_create_data_command.py create-data semantickitti --root-path data/semantickitti --out-dir data/semantickitti --extra-tag semantickitti
```

### Converted outputs

Expected outputs are `semantickitti_infos_train.pkl`, `semantickitti_infos_val.pkl`, and `semantickitti_infos_test.pkl` next to `sequences/`.

## S3DIS

### Source and preconvert layout

Before MMDetection3D conversion, export S3DIS rooms with the dataset-provided collection scripts. The acquired source layout is:

```text
s3dis/
├── meta_data/
├── Stanford3dDataset_v1.2_Aligned_Version/
│   ├── Area_1/
│   ├── ...
│   └── Area_6/
├── collect_indoor3d_data.py
├── indoor3d_util.py
└── README.md
```

The export step creates room-level point, semantic-label, and instance-label arrays. Run MMDetection3D conversion only after those exported files exist.

### Command family

```bash
python ../scripts/build_create_data_command.py create-data s3dis --root-path data/s3dis --out-dir data/s3dis --extra-tag s3dis --workers 4
```

### Converted outputs

Expected outputs include `points/`, `instance_mask/`, `semantic_mask/`, `seg_info/`, and `s3dis_infos_Area_1.pkl` through `s3dis_infos_Area_6.pkl`. `seg_info` contains per-area label weights and resampled scene indices used by segmentation configs.

## ScanNet

### Source and preconvert layout

The acquired source layout is:

```text
scannet/
├── meta_data/
├── scans/
├── scans_test/
├── batch_load_scannet_data.py
├── load_scannet_data.py
├── scannet_utils.py
└── README.md
```

Run the ScanNet export script first to generate `scannet_instance_data/`. Optional RGB export creates `posed_images/` with image files, camera poses, and `intrinsic.txt` per scene.

### Command family

```bash
python ../scripts/build_create_data_command.py create-data scannet --root-path data/scannet --out-dir data/scannet --extra-tag scannet --workers 4
```

### Converted outputs

Expected outputs include `points/`, `instance_mask/`, `semantic_mask/`, `seg_info/`, `scannet_infos_train.pkl`, `scannet_infos_val.pkl`, and `scannet_infos_test.pkl`. ScanNet stores unaligned points plus an `axis_align_matrix`; detection pipelines usually apply global alignment during preprocessing.

## SUN RGB-D

### Source and preconvert layout

Initial source layout:

```text
sunrgbd/
├── matlab/
│   ├── extract_split.m
│   ├── extract_rgbd_data_v1.m
│   └── extract_rgbd_data_v2.m
└── OFFICIAL_SUNRGBD/
    ├── SUNRGBD/
    ├── SUNRGBDMeta2DBB_v2.mat
    ├── SUNRGBDMeta3DBB_v2.mat
    └── SUNRGBDtoolbox/
```

After MATLAB extraction and before `create_data.py`, expect:

```text
sunrgbd_trainval/
├── calib/
├── depth/
├── image/
├── label/
├── label_v1/
├── seg_label/
├── train_data_idx.txt
└── val_data_idx.txt
```

MMDetection3D v1.4.0 uses the v1 labels for training/testing.

### Command family

```bash
python ../scripts/build_create_data_command.py create-data sunrgbd --root-path data/sunrgbd --out-dir data/sunrgbd --extra-tag sunrgbd --workers 4
```

### Converted outputs

Expected outputs are `points/`, `sunrgbd_infos_train.pkl`, and `sunrgbd_infos_val.pkl`. Info files include depth-coordinate point-cloud metadata, image metadata under `CAM0`, and 2D/3D annotations.

## Info migrations

### v2 info-file migration

Use the v2 migration command when info pickles were generated by early v1.0.0 release candidates and need the `metainfo`/`data_list` layout used by current v1.x configs.

```bash
python ../scripts/build_create_data_command.py update-infos --dataset kitti --pkl-path data/kitti/kitti_infos_trainval.pkl --out-dir data/kitti_v2_infos
```

Supported dataset names are `kitti`, `waymo`, `scannet`, `sunrgbd`, `lyft`, `nuscenes`, and `s3dis`. Prefer a separate `--out-dir` until the migrated file is inspected.

### Coordinate-refactor migration

The older coordinate-update helper modifies different files per dataset and may overwrite data if `out-dir` equals `root-dir`. Render it only after confirming the user really has pre-refactor coordinate pickles:

```bash
python ../scripts/build_create_data_command.py update-coords --dataset nuscenes --root-dir data/nuscenes --out-dir data/nuscenes_coord_updated --version v1.0
```

Dataset effects: KITTI and Waymo update only database-info pickles; NuScenes and Lyft update lidar-coordinate infos; SUN RGB-D updates depth-coordinate yaws; ScanNet/S3DIS are effectively unaffected by that helper.
