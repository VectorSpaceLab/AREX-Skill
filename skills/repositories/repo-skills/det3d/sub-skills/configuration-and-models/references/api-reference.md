# Det3D Configuration and Model API Reference

This reference records the callable contracts needed for safe inspection and,
only after dependency validation, model construction. It intentionally avoids
requiring a dataset or a training run.

## Config loader

```python
from det3d.torchie import Config
cfg = Config.fromfile("path/to/config.py")
```

`Config.fromfile` expands the path, requires it to exist, and supports Python,
JSON, and YAML extensions. A Python config is imported by basename after its
directory is temporarily placed on `sys.path`; dots in the basename are
rejected. The file is executable Python. Public values are exposed both by
mapping access (`cfg["model"]`) and attribute access (`cfg.model`). Missing
attribute keys raise `AttributeError`; missing mapping keys raise `KeyError`.

`Config` is a loader/container, not a general inheritance or merge system. The
source does not implement `_base_` resolution. Treat values created by imports,
function calls, `range`, loggers, and path expressions as potentially
non-serializable until checked.

## Model registries

`det3d.models.registry` defines these registries:

| Registry | Representative registered types |
| --- | --- |
| `DETECTORS` | `SingleStageDetector`, `VoxelNet`, `PointPillars` |
| `READERS` | `VFELayer`, `VoxelFeatureExtractor`, `VoxelFeatureExtractorV2`, `VFEV3_ablation`, `VoxelFeatureExtractorV3`, `SimpleVoxel`, `PillarFeatureNet` |
| `BACKBONES` | `ResNet`, `SpMiddleFHD`, `SpMiddleFHDNobn`, `SpMiddleResNetFHD`, `RCNNSpMiddleFHD`, `PointPillarsScatter` |
| `NECKS` | `RPN`, `PointModule`, `FPN` |
| `HEADS` | `Head`, `RegHead`, `MultiGroupHead` |
| `LOSSES` | registered loss classes including focal, smooth-L1, cross-entropy, IoU, and weighted variants |

`det3d.models.__init__` imports component packages to populate the registries.
That import is not construction, but it can fail before registration when
optional packages such as spconv or compiled operators are unavailable.

The underlying `Registry` stores classes by exact class name. `get(key)`
returns `None` for an unknown key. Duplicate registration raises `KeyError`.

## Generic builder

```python
from det3d.utils import build_from_cfg
obj = build_from_cfg({"type": "RPN", ...}, NECKS)
```

The config must be a dict-like object with `type`. A string type is looked up
exactly in the selected registry; a class object is accepted directly. Default
arguments fill only missing keys. Unknown strings raise `KeyError`, malformed
types raise `TypeError`, and the selected class is instantiated with remaining
keyword arguments.

`det3d.models.builder` wraps this behavior:

```python
build_reader(cfg)
build_backbone(cfg)
build_neck(cfg)
build_head(cfg)
build_loss(cfg)
build_detector(cfg, train_cfg=None, test_cfg=None)
```

A list passed to a wrapper is converted into `nn.Sequential`. `build_detector`
passes `train_cfg` and `test_cfg` as default constructor arguments; it does not
build a dataset, dataloader, optimizer, or checkpoint.

## Detector construction contract

A single-stage detector config normally has:

```python
model = dict(
    type="VoxelNet" or "PointPillars",
    reader={...},
    backbone={...},
    neck={...},
    bbox_head={...},
)
```

`SingleStageDetector` builds the reader, backbone, optional neck, and head in
that order. `VoxelNet.forward` expects voxelized keys such as `voxels`,
`coordinates`, `num_points`, `num_voxels`, and `shape`; `PointPillars.forward`
uses the same outer example keys but passes coordinates to its pillar reader.
The returned predictions are consumed by `MultiGroupHead` for loss or decode.
These are runtime tensor contracts, not safe-inspection inputs.

## Core non-registry builders

- `det3d.builder.build_box_coder(cfg)` supports `ground_box3d_coder` and
  `bev_box_coder`; unsupported values raise `ValueError`.
- `build_anchor_generator(cfg)` supports `anchor_generator_stride`,
  `anchor_generator_range`, and `bev_anchor_generator_range`.
- `build_similarity_metric(cfg)` supports rotate-IoU, nearest-IoU, and distance
  similarity variants.
- `AssignTarget` builds anchor generators, a similarity calculator, a shared
  box coder, and one `TargetAssigner` per task while the data pipeline is
  constructed. This is not part of safe model-only inspection.

## Checkpoint API

```python
from det3d.torchie.trainer import load_checkpoint
checkpoint = load_checkpoint(model, filename, map_location="cpu", strict=False)
```

Accepted filenames include local files and supported URL schemes. A local
checkpoint must be an `OrderedDict` state dict or a dict containing
`state_dict`; otherwise loading raises. A leading `module.` prefix is stripped.
`load_state_dict` reports unexpected, missing, and shape-mismatched keys;
`strict=True` raises on those mismatches.

`save_checkpoint` writes `meta` and CPU `state_dict`, plus optimizer state when
provided. In the training workflow, `checkpoint_config.meta` is populated with
Det3D version, config text, and dataset class names. Use metadata to check the
class/order and architecture contract before loading weights.
