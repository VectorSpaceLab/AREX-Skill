# Dataset Workflows

## Registry and config coupling

OpenPCDet imports these dataset classes through `pcdet.datasets.__all__`:

- `KittiDataset`
- `NuScenesDataset`
- `WaymoDataset`
- `PandasetDataset`
- `LyftDataset`
- `ONCEDataset`
- `Argo2Dataset`
- `CustomDataset`

Each model config points to a dataset config under `tools/cfgs/dataset_configs/`. Always load the exact model config and inspect `DATA_CONFIG.DATASET`, `DATA_CONFIG.DATA_PATH`, `INFO_PATH`, `DATA_SPLIT`, `POINT_FEATURE_ENCODING`, `DATA_PROCESSOR`, and optional database sampler settings.

From the generated skill root, use the bundled root helper to summarize configs:

```bash
python scripts/summarize_openpcdet_config.py --cfg <config.yaml>
```

## Dataset map

| Dataset | Dataset class | Main generated products | Common prerequisites |
|---|---|---|---|
| KITTI | `KittiDataset` | `kitti_infos_train.pkl`, `kitti_infos_val.pkl`, `kitti_infos_test.pkl`, `kitti_dbinfos_train.pkl`, ground-truth database folder | `training/velodyne`, `training/label_2`, `training/calib`, `ImageSets` |
| NuScenes | `NuScenesDataset` | `nuscenes_infos_*.pkl`, optional database info | NuScenes version folders, samples, sweeps, official metadata/devkit |
| Waymo | `WaymoDataset` | processed sequences, `waymo_infos_*.pkl`, database info | raw Waymo sequences converted to OpenPCDet format, sufficient workers/storage |
| Lyft | `LyftDataset` | `lyft_infos_*.pkl`, database info | Lyft devkit/versioned folders, sweeps |
| ONCE | `ONCEDataset` | `once_infos_*.pkl`, database info | ONCE data and split files |
| Pandaset | `PandasetDataset` | `pandaset_infos_*.pkl`, database info | Pandaset SDK/data layout |
| Argoverse2 | `Argo2Dataset` | `argo2_infos_*.pkl`, optional saved bin intermediates | av2/kornia dependencies and expected sensor layout |
| Custom | `CustomDataset` | `custom_infos_*.pkl`, `custom_dbinfos_*.pkl`, ground-truth database | point clouds, labels/info schema, `ImageSets`, custom YAML |

## Command planning

Use the bundled command builder from the generated skill root:

```bash
python scripts/plan_openpcdet_command.py --repo <checkout> --mode kitti-infos --cfg <dataset-config.yaml>
python scripts/plan_openpcdet_command.py --repo <checkout> --mode nuscenes-infos --cfg <dataset-config.yaml>
python scripts/plan_openpcdet_command.py --repo <checkout> --mode waymo-infos --cfg <dataset-config.yaml>
python scripts/plan_openpcdet_command.py --repo <checkout> --mode custom-infos --cfg <dataset-config.yaml>
```

The helper prints by default. Add `--execute` only after paths, disk space, and expected products are confirmed.

## Layout checking

From the generated skill root, run the sub-skill layout checker before conversion:

```bash
python sub-skills/data-preparation/scripts/check_openpcdet_dataset_layout.py --dataset kitti --root <data-root>
```

A missing info/database product is expected before first conversion, but missing raw folders usually means the config `DATA_PATH` or dataset root is wrong.

## Database sampler consistency

When a config has database sampling enabled:

- `DB_INFO_PATH` must point to a database info pickle generated from the same training split.
- `DB_DATA_PATH` must point to the matching objects folder.
- `PREPARE.filter_by_min_points` class keys must match `CLASS_NAMES`.
- Reusing KITTI database products with custom classes or custom point features is invalid.

## CustomDataset minimum expectations

CustomDataset follows the same internal `DatasetTemplate` pipeline, so custom tasks need:

- A custom dataset YAML with `DATASET: CustomDataset` and correct `DATA_PATH`.
- `POINT_FEATURE_ENCODING.used_feature_list` and `src_feature_list` matching the point files.
- Info pickle records containing point-cloud paths, frame ids, annotations, and class names expected by `CustomDataset`.
- Optional ground-truth database generated after info creation if database sampling is enabled.

Route custom `.bin`/`.npy` demo-only checks to `../inference-and-custom-data/SKILL.md`.
