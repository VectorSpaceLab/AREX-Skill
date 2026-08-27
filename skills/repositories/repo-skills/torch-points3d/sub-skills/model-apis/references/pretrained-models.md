# Pretrained Models and Checkpoint-backed APIs

## Purpose

Read this before using Torch Points3D pretrained helpers. These helpers can
perform network downloads and checkpoint file writes, so they are not safe as an
automatic smoke test unless the user accepts those side effects.

## Public API

The public class is spelled `PretainedRegistry` in the package.

Verified signatures:

```python
PretainedRegistry.from_pretrained(model_tag, download=True, out_file=None, weight_name="latest", mock_dataset=True)
PretainedRegistry.from_file(path, weight_name="latest", mock_property=None)
PretainedRegistry.available_models()
```

## Available tag families

`available_models()` returns keys for these families:

- PointNet2 S3DIS folds: `pointnet2_largemsg-s3dis-1` through `pointnet2_largemsg-s3dis-6`.
- RSConv S3DIS folds: `rsconv-s3dis-1` through `rsconv-s3dis-6`.
- KPConv S3DIS folds: `kpconv-s3dis-1` through `kpconv-s3dis-6`.
- Sparse/Minkowski S3DIS folds: `minkowski-res16-s3dis-1` through `minkowski-res16-s3dis-6`.
- Registration models: `minkowski-registration-3dmatch`, `minkowski-registration-kitti`, and `minkowski-registration-modelnet`.
- Panoptic example: `pointgroup-scannet`.

Always print the registry in the target environment because future repository
versions may add or remove tags:

```python
from torch_points3d.applications.pretrained_api import PretainedRegistry
print(sorted(PretainedRegistry.available_models()))
```

## `from_pretrained` behavior

- If `model_tag` is unknown, the helper raises an exception and includes the available model list.
- With `download=True` (default), it downloads a `.pt` checkpoint from a W&B-hosted URL into the package's internal weights directory.
- `weight_name` defaults to `"latest"` when `None`.
- With `mock_dataset=True` (default), the helper uses checkpoint dataset properties plus hard-coded fallback properties such as `feature_dimension` and `num_classes` for many S3DIS models.
- With `mock_dataset=False`, it calls `instantiate_dataset(checkpoint.data_config)`, which can require real dataset files and transforms.
- `out_file` is present in the signature but the implementation overwrites it with an internal weights path based on `model_tag`; do not rely on it as a destination override for this snapshot.

## `from_file` behavior

`from_file(path, weight_name="latest", mock_property=None)` loads a local
Torch Points3D checkpoint through `ModelCheckpoint`. If `mock_property` is not
provided, it instantiates the dataset from the checkpoint data config; that may
require local dataset files. Provide `mock_property` when you only need to build
a model for inspection and know the required dataset properties.

## Safe usage pattern

```python
from torch_points3d.applications.pretrained_api import PretainedRegistry

models = sorted(PretainedRegistry.available_models())
print(models[:5])
# Ask before downloading or before using a checkpoint path supplied by a user.
```

Then, after network/file side effects are approved:

```python
model = PretainedRegistry.from_pretrained(
    "pointnet2_largemsg-s3dis-1",
    download=True,
    weight_name="latest",
    mock_dataset=True,
)
model.eval()
```

## Backend cautions

Sparse/Minkowski and registration tags still need their model backends. A tag
being present in the registry is not proof that the target environment can load
or run it. Probe optional backends before loading these tags.
