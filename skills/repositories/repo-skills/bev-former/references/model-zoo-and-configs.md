# Model Zoo and Config Map

## Purpose

Read this when you need a quick overview of the published BEVFormer families, the main config knobs, or the difference between BEVFormer and BEVFormerV2 configs.

## Config Families

| Family | Representative config | Distinctive knobs | Notes |
| --- | --- | --- | --- |
| BEVFormer-tiny | `projects/configs/bevformer/bevformer_tiny.py` | `queue_length=3`, `bev_h=50`, `bev_w=50`, `use_can_bus=True`, `model.type='BEVFormer'` | Parsed successfully during skill construction; smaller camera-only baseline. |
| BEVFormer-small | `projects/configs/bevformer/bevformer_small.py` | R101-DCN backbone, heavier memory use than tiny | Documented in the README model zoo. |
| BEVFormer-base | `projects/configs/bevformer/bevformer_base.py` | R101-DCN baseline | Documented in the README model zoo and used in the getting-started train/eval examples. |
| BEVFormer-tiny_fp16 | `projects/configs/bevformer_fp16/bevformer_tiny_fp16.py` | FP16 training route for the tiny variant | Documented in the README model zoo and linked from the FP16 training path. |
| BEVFormerV2 t1-base | `projects/configs/bevformerv2/bevformerv2-r50-t1-base-24ep.py` | `dataset_type='CustomNuScenesDatasetV2'`, `frames=(0,)`, `mono_cfg`, `PerceptionTransformerV2`, `DD3DMapper` | Parsed successfully during skill construction. |
| BEVFormerV2 t1/t2/t8 | `projects/configs/bevformerv2/*` | Multi-frame V2 variants with longer or denser temporal settings | Documented in the README model zoo. |

## Common Config Signals

- `plugin = True` and `plugin_dir = 'projects/mmdet3d_plugin/'` identify the repo-local OpenMMLab plugin.
- `data_root = 'data/nuscenes/'` and `ann_file = '...nuscenes_infos_temporal_*.pkl'` point at the expected nuScenes layout.
- BEVFormer V1 configs usually use `CustomNuScenesDataset`, `use_camera=True`, `use_lidar=False`, and `use_can_bus=True`.
- BEVFormerV2 configs usually use `CustomNuScenesDatasetV2`, `frames`, `mono_cfg`, `num_mono_levels`, and `DD3DMapper`.
- The backbone, BEV size, queue length, and transformer depth determine most memory and throughput differences between config families.

## Read Before Editing

- Use `sub-skills/installation-and-configs/SKILL.md` when you need to choose or modify a config.
- Use `sub-skills/installation-and-configs/scripts/inspect_bevformer_config.py` for a safe static summary of a config file.
- Use `sub-skills/dataset-preparation/SKILL.md` when a config change depends on a different nuScenes or CAN-bus layout.
