# OpenPCDet Overview for Operators

## Package shape

OpenPCDet provides the `pcdet` package plus checkout-level workflow scripts. The package contains reusable registries, datasets, models, CUDA ops, utilities, and config loaders. The checkout scripts orchestrate full workflows.

Important runtime surfaces:

- Config loader: `pcdet.config.cfg_from_yaml_file`, `pcdet.config.cfg_from_list`, global `pcdet.config.cfg`.
- Dataset factory: `pcdet.datasets.build_dataloader` and dataset registry names `KittiDataset`, `NuScenesDataset`, `WaymoDataset`, `PandasetDataset`, `LyftDataset`, `ONCEDataset`, `Argo2Dataset`, `CustomDataset`.
- Model factory: `pcdet.models.build_network` and detector registry names `SECONDNet`, `PartA2Net`, `PVRCNN`, `PointPillar`, `PointRCNN`, `SECONDNetIoU`, `CaDDN`, `VoxelRCNN`, `CenterPoint`, `PVRCNNPlusPlus`, `MPPNet`, `MPPNetE2E`, `PillarNet`, `VoxelNeXt`, `TransFusion`, `BevFusion`.
- Native CUDA ops: IoU/NMS, ROI-aware pooling, ROI point pooling, PointNet++ stack/batch, BEV pool, in-group indices.

## Workflow entry point semantics

Use the bundled command builder (`scripts/plan_openpcdet_command.py`) to construct commands for an OpenPCDet checkout rather than copying command lines by memory.

Common workflow roles:

- Training reads one YAML config, creates output under `output/<config-group>/<config-name>/<extra_tag>/`, writes logs/checkpoints/tensorboard, resumes from `--ckpt` or latest checkpoint if present, then optionally evaluates the last checkpoints.
- Evaluation reads a YAML config and checkpoint or checkpoint directory, builds a test dataloader/model, and writes logs/results under the config-specific `output/.../eval/` subtree.
- Demo inference reads one config, one checkpoint, and one point-cloud file or directory (`.bin` float32 reshaped to `N x 4`, or `.npy` 2-D array), then visualizes predictions through Open3D or Mayavi.
- Dataset preparation uses dataset-module entrypoints to produce info pickle files and, when supported, ground-truth database files for database sampling.

## Config group map

The construction snapshot contained 67 YAML configs:

- `tools/cfgs/dataset_configs/`: 9 dataset schemas.
- `tools/cfgs/kitti_models/`: 16 model configs.
- `tools/cfgs/nuscenes_models/`: 10 model configs, including BEVFusion/TransFusion/CenterPoint/DSVT-style workloads.
- `tools/cfgs/waymo_models/`: 22 model configs, including MPPNet and VoxelNeXt variants.
- `tools/cfgs/once_models/`: 5 model configs.
- `tools/cfgs/lyft_models/`: 2 model configs.
- `tools/cfgs/custom_models/`: 2 custom-data configs.
- `tools/cfgs/argo2_models/`: 1 Argoverse2 config.

## High-risk coupling points

- The PyTorch CUDA version, local CUDA toolkit headers, spconv wheel suffix, GPU compute capability, and OpenPCDet extension build must align.
- `DATA_CONFIG.DATASET`, `DATA_CONFIG.DATA_PATH`, generated info pickle names, `CLASS_NAMES`, and checkpoint classes must match.
- `cfg_from_list` enforces type compatibility; string overrides that look valid can fail if they do not match the original config value type.
- BEVFusion/CaDDN-style image-aware configs need image files/calibration/extra image dependencies and cannot be validated by LiDAR-only smoke tests.
- Waymo/NuScenes/Lyft/Argo2 converters require their official devkits/data layouts; failures are often missing optional packages or mismatched versioned metadata.
