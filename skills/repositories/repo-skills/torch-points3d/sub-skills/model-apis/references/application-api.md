# Application API Reference

## Purpose

Read this when using Torch Points3D as a Python library instead of via Hydra
training scripts. The facts below were verified from source and installed
signature inspection for the repository snapshot captured in this skill.

## Verified constructors

| API | Signature | Backend/input style | Notes |
| --- | --- | --- | --- |
| `PointNet2` | `(architecture: str = None, input_nc: int = None, num_layers: int = None, config: DictConfig = None, multiscale=False, *args, **kwargs)` | Dense `[B, N, C]` features and `[B, N, 3]` positions | `multiscale` affects which default config file is loaded (`ss`/`ms`). `output_nc` in `kwargs` adds a 1D-conv head. |
| `KPConv` | `(architecture: str = None, input_nc: int = None, num_layers: int = None, config: DictConfig = None, *args, **kwargs)` | Partial-dense PyG geometric data | Common kwargs include `in_grid_size`, `in_feat`, and `output_nc`. Needs `torch-points-kernels`. |
| `RSConv` | `(architecture: str = None, input_nc: int = None, num_layers: int = None, config: DictConfig = None, *args, **kwargs)` | Dense `[B, N, C]` features and `[B, N, 3]` positions | `output_nc` adds a head. Tests cover `unet` and `encoder` paths. |
| `SparseConv3d` | `(architecture: str = None, input_nc: int = None, num_layers: int = None, config: DictConfig = None, backend: str = 'minkowski', *args, **kwargs)` | Sparse coordinates/features | Selects `backend` or `SPARSE_BACKEND`; needs `MinkowskiEngine` or `torchsparse`. |
| `Minkowski` | Optional application module | MinkowskiEngine sparse tensors | Importing this module fails if `MinkowskiEngine` is not installed. |

The underlying `ModelFactory` requires `architecture` and lowercases it. Valid
values are `"unet"`, `"encoder"`, and `"decoder"`, but individual factories may
not implement every value. When `config` is omitted, the factory loads built-in
application configs packaged with `torch_points3d.applications/conf/...`.

## Dense PointNet2 pattern

```python
import torch
from torch_geometric.data import Batch, Data
from torch_points3d.applications.pointnet2 import PointNet2

num_points = 1024
input_nc = 5
output_nc = 10
pos = torch.randn((num_points, 3)).unsqueeze(0)   # [1, N, 3]
x = torch.randn((num_points, input_nc)).unsqueeze(0)  # [1, N, C]
batch = Batch.from_data_list([Data(pos=pos, x=x), Data(pos=pos.clone(), x=x.clone())])
model = PointNet2(architecture="unet", input_nc=input_nc, num_layers=3, output_nc=output_nc)
out = model(batch)
assert out.x.shape[1] == output_nc
```

PointNet2 and RSConv call `_set_input` methods that assert `len(data.pos.shape)
== 3` and transpose `data.x` from `[B, N, C]` to `[B, C, N]` internally.

## KPConv pattern

KPConv expects PyG-style geometric data rather than the dense batch-major shape.
A minimal input has `pos`, `x`, and `batch` after batching. Typical configs use
`GridSampling3D` before the forward pass and may use precomputed multi-scale
neighbors for training speed.

```python
import torch
from torch_geometric.data import Batch, Data
from torch_points3d.core.data_transform import GridSampling3D
from torch_points3d.applications.kpconv import KPConv

points = Data(pos=torch.randn(128, 3), x=torch.randn(128, 3))
points = GridSampling3D(0.01)(points)
batch = Batch.from_data_list([points, points.clone()])
model = KPConv(architecture="unet", input_nc=3, in_feat=16, in_grid_size=0.02, num_layers=4)
out = model(batch)
```

If this fails inside a compiled op, validate `torch-points-kernels`,
`torch-cluster`, `torch-scatter`, and `torch-sparse` first.

## SparseConv3d pattern

Sparse models require quantized coordinates and a sparse backend:

```python
from torch_points3d.applications.sparseconv3d import SparseConv3d
model = SparseConv3d(architecture="unet", input_nc=3, num_layers=4, backend="minkowski")
```

The constructor checks `SPARSE_BACKEND`; if the environment variable names a
valid backend it overrides the function's `backend` argument. Do not set it to a
backend whose package cannot import.

## Model config factory

Hydra workflows use `torch_points3d.models.model_factory.instantiate_model(config,
dataset)`. It expects:

- `config.data.task`, such as `segmentation`, `classification`, `registration`, `object_detection`, or `panoptic`.
- `config.model_name`, matching a key under `config.models`.
- `config.models.<model_name>.class`, such as `pointnet2.PointNet2_D`, `kpconv.KPConvPaper`, or `rsconv.RSConvLogicModel`.

If `model_name` is absent, the factory raises an exception listing available
keys. If the class cannot be found, check task/model file alignment before
editing model code.

## Output head behavior

The high-level application APIs optionally add a small MLP/Conv head when
`output_nc` is present in `kwargs`. Use this for standalone feature extraction
or smoke checks where you need a predictable channel count. Without `output_nc`,
`output_nc` comes from the selected built-in config and can differ by model,
architecture, and `in_feat`.
