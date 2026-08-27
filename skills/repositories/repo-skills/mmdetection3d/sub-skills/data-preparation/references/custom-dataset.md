# Custom Dataset Preparation

This reference covers custom data layout and schema decisions for MMDetection3D v1.4.0. Use it before touching model configs or adding custom components.

## Version-specific gate

Do not blindly run a `create_data.py custom` command in v1.4.0. The dataset-customization guide presents that command shape, but the inspected v1.4.0 dispatcher only implements `kitti`, `waymo`, `nuscenes`, `lyft`, `semantickitti`, `s3dis`, `scannet`, and `sunrgbd`. For custom data, either:

1. reorganize data into a supported dataset format such as KITTI-style data and use the corresponding converter, or
2. implement/supply a custom converter that writes v2-style info pickles, then implement/register a dataset class and config.

The bundled command builder intentionally refuses to render a built-in `custom` conversion command. The bundled layout checker can still validate custom raw layouts.

## Basic raw data formats

### Point clouds

- Training and inference pipelines expect point clouds stored as `.bin` when using `LoadPointsFromFile` in the usual custom-data path.
- The common LiDAR convention is float32 rows with at least `[x, y, z, intensity]`; align `load_dim` and `use_dim` in the config with the actual columns.
- Convert `.pcd`, `.las`, or vendor-specific formats to `.bin` outside the safe helper scripts. Verify shape and dtype before writing an info pickle.

### 3D labels

A minimal text-label line can be organized as:

```text
x y z dx dy dz yaw category_name
1.23 1.42 0.23 3.96 1.65 1.55 1.56 Car
3.51 2.15 0.42 1.05 0.87 1.86 1.23 Pedestrian
```

Keep all boxes in one declared 3D coordinate system. Record whether the box type is `LiDAR`, `Camera`, or `Depth`, and keep dimension/yaw conventions consistent from converter to dataset class to evaluator.

### Calibration

For vision or multi-modality datasets, calibration text files should carry camera intrinsics and transforms from LiDAR to each camera. A common minimal pattern is:

```text
P0
P1
P2
...
lidar2cam0
lidar2cam1
lidar2cam2
...
```

The exact numeric serialization is converter-defined, but the generated info pickle must contain the matrices that loaders and visualizers need (`cam2img`, `lidar2cam`, `lidar2img`, or the equivalent for the selected coordinate mode).

## Raw layout templates

Use [`../scripts/check_dataset_layout.py`](../scripts/check_dataset_layout.py) to validate these folders with `--dataset custom --custom-task ...`.

### LiDAR 3D detection

```text
custom/
├── ImageSets/
│   ├── train.txt
│   └── val.txt
├── points/
│   ├── 000000.bin
│   └── 000001.bin
└── labels/
    ├── 000000.txt
    └── 000001.txt
```

Use this when each sample needs point clouds and 3D boxes only.

### Vision 3D detection

```text
custom/
├── ImageSets/
│   ├── train.txt
│   └── val.txt
├── calibs/
│   ├── 000000.txt
│   └── 000001.txt
├── images/
│   ├── images_0/
│   ├── images_1/
│   └── images_2/
└── labels/
    ├── 000000.txt
    └── 000001.txt
```

Use this when the model uses images and camera geometry but not point clouds.

### Multi-modality 3D detection

```text
custom/
├── ImageSets/
│   ├── train.txt
│   └── val.txt
├── calibs/
├── points/
├── images/
│   ├── images_0/
│   ├── images_1/
│   └── images_2/
└── labels/
```

Use this when LiDAR points, images, and calibrations are all required.

### LiDAR semantic segmentation

```text
custom/
├── ImageSets/
│   ├── train.txt
│   └── val.txt
├── points/
│   ├── 000000.bin
│   └── 000001.bin
└── semantic_mask/
    ├── 000000.bin
    └── 000001.bin
```

The semantic mask must align one label per point after any point filtering or resampling decision made by the converter.

## Info-pickle expectations

Current v1.x info pickles should be dictionaries with:

- `metainfo`: dataset-level metadata such as `dataset`, `categories` or `classes`, and info-version notes.
- `data_list`: one dictionary per sample.

For a LiDAR detection sample, typical `data_list` fields are:

```python
{
    'sample_idx': '000000',
    'lidar_points': {
        'lidar_path': 'points/000000.bin',
        'num_pts_feats': 4,
    },
    'instances': [
        {
            'bbox_3d': [x, y, z, dx, dy, dz, yaw],
            'bbox_label_3d': 0,
        }
    ],
}
```

For image or multi-modality samples, add an `images` dictionary with per-camera paths and camera matrices. For segmentation samples, add `pts_semantic_mask_path`; for instance segmentation, add `pts_instance_mask_path` as needed. Keep paths relative to `data_root` where possible so configs remain portable.

## Dataset class and config checklist

A custom dataset usually extends `Det3DDataset` or the closest existing dataset class and registers itself in the dataset registry. The class should declare `METAINFO`, parse annotations into the expected 3D box class, and handle empty annotations safely.

Minimum config items to review:

- `dataset_type`: registered dataset class name.
- `data_root`: root that contains the custom layout or generated info files.
- `metainfo` / `class_names`: exactly match label ids in the info pickle.
- `ann_file`: e.g. `custom_infos_train.pkl` and `custom_infos_val.pkl`.
- `data_prefix`: e.g. `dict(pts='points')`, camera prefixes, or mask prefixes.
- `box_type_3d`: `LiDAR`, `Camera`, or `Depth`.
- Loading pipeline: `LoadPointsFromFile`, `LoadImageFromFileMono3D`, `LoadMultiViewImageFromFiles`, `LoadAnnotations3D`, and `Pack3DDetInputs` must request keys that the info pickle actually contains.
- `load_dim` and `use_dim`: must match the `.bin` point format.
- `point_cloud_range`, `voxel_size`, anchor ranges/sizes, and output shapes: route detailed model adaptation to `configuration-model-zoo`.
- Evaluator: v1.4.0 custom-dataset guidance only documents KITTI-style evaluation for custom 3D detection; other custom metrics require implementation.

## Validation flow for future agents

1. Ask for the dataset task type: `lidar-det`, `vision-det`, `multimodal-det`, or `lidar-seg`.
2. Check the raw layout:

   ```bash
   python ../scripts/check_dataset_layout.py custom --custom-task lidar-det --root data/custom --stage preconvert
   ```

3. Confirm point dtype/shape and label-coordinate convention. The layout checker cannot verify numeric correctness.
4. Decide whether to adapt a supported converter or write a custom converter. Do not claim a built-in custom dispatcher unless the user's checkout has one.
5. After generating info pickles, inspect one sample for `metainfo`, `data_list`, relative paths, box dimensions, labels, and camera/point keys.
6. Only then move to dataset class/config/training work.

## Common custom-data pitfalls

- `.bin` point files written as float64 or with unexpected columns while the config says `load_dim=4`.
- Label category strings do not match `class_names`, or label ids are not contiguous from zero.
- Boxes are written in camera/depth coordinates but the config uses `box_type_3d='LiDAR'`.
- `yaw`, length/width/height order, or box origin differs between converter and box class.
- `ImageSets/*.txt` contains ids that do not have matching point/image/label files.
- Info pickle paths are absolute or machine-specific instead of portable under `data_root`.
- Camera intrinsics/extrinsics are missing for image or multi-modality pipelines.
- Empty scenes are not handled; `parse_ann_info` should return empty arrays with correct shapes and dtypes.
- Evaluator choice is copied from another dataset without verifying supported fields.
