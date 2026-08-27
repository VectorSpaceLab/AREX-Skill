# Config and Model Map

## Config loader behavior

OpenPCDet uses a global EasyDict config object.

- `cfg_from_yaml_file(path, cfg)` loads YAML and recursively merges `_BASE_CONFIG_` if present.
- `cfg_from_list(overrides, cfg)` applies CLI `--set` overrides as key/value pairs.
- Override keys must exist.
- Override values must match the existing value's type unless the target is an EasyDict or list with special conversion logic.
- `cfg.ROOT_DIR` is set from the installed package location, but checkout scripts usually run from a repository checkout and use checkout-relative configs/data.

From the generated skill root, use the root summarizer before editing overrides:

```bash
python scripts/summarize_openpcdet_config.py --cfg <config.yaml> --set KEY VALUE
```

## Detector registry names

The construction snapshot verified these detector registry names:

- `SECONDNet`
- `PartA2Net`
- `PVRCNN`
- `PointPillar`
- `PointRCNN`
- `SECONDNetIoU`
- `CaDDN`
- `VoxelRCNN`
- `CenterPoint`
- `PVRCNNPlusPlus`
- `MPPNet`
- `MPPNetE2E`
- `PillarNet`
- `VoxelNeXt`
- `TransFusion`
- `BevFusion`

The YAML field `MODEL.NAME` must match one of these names unless the user added a new detector and registered it.

## Dataset registry names

The construction snapshot verified these dataset registry names:

- `KittiDataset`
- `NuScenesDataset`
- `WaymoDataset`
- `PandasetDataset`
- `LyftDataset`
- `ONCEDataset`
- `Argo2Dataset`
- `CustomDataset`

The YAML field `DATA_CONFIG.DATASET` must match one of these names unless the user added a dataset and registered it.

## Model-family routing

| Family | Typical config groups | Notes |
|---|---|---|
| PointPillar/SECOND/Part-A2 | KITTI, custom | Classic voxel/pillar baselines; depend on spconv and native ops. |
| PV-RCNN / PV-RCNN++ / Voxel R-CNN | KITTI, Waymo | Two-stage models with ROI/pooling ops; checkpoint/config coupling is strict. |
| CenterPoint / TransFusion / VoxelNeXt | NuScenes/Waymo/ONCE/Lyft | Modern center-based or sparse-conv families; sweeps and point range matter. |
| BEVFusion / CaDDN | NuScenes/KITTI image-aware configs | Need image/camera data, calibration, image transforms, and extra memory. |
| MPPNet | Waymo | Multi-frame temporal model; requires sequence frames and memory-bank-specific config behavior. |
| DSVT-style configs | Waymo/NuScenes | Transformer/sparse backbones; runtime and memory budgets are higher than simple baselines. |

## Extension points

When adding a new detector/model:

1. Implement the class under the relevant `pcdet.models` subtree.
2. Register it in the appropriate `__init__.py` `__all__` mapping.
3. Create or adapt a YAML config with `MODEL.NAME` set to the registered class name.
4. Ensure each module `NAME` field maps to an implemented VFE/backbone/head component.
5. Run config summary and a model-build smoke only after runtime/data prerequisites are satisfied.

When adding a new dataset:

1. Implement a `DatasetTemplate` subclass.
2. Register it in `pcdet.datasets.__all__` and import it in `pcdet.datasets.__init__`.
3. Provide dataset config YAML and info generation path.
4. Update class names, splits, point feature encoding, processors, and database sampler products.

## Advanced config caveats

- BEVFusion and CaDDN introduce image branches; LiDAR-only dataset checks are insufficient.
- MPPNet uses temporal context; single-frame smoke tests do not prove training correctness.
- VoxelNeXt/DSVT/sparse-conv configs are sensitive to spconv version and GPU memory.
- `DATA_PROCESSOR` order matters; changing voxel size/range without adjusting model head/grid assumptions can silently corrupt geometry.
