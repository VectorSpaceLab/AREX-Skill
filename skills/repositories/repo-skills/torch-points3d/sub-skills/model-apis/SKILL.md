---
name: model-apis
description: "Use Torch Points3D high-level model factories, application APIs,
  pretrained registry helpers, and dense or sparse backend smoke tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Torch Points3D Model APIs

Use this sub-skill when the user asks to instantiate or debug Torch Points3D
model APIs directly in Python, run a standalone forward pass, inspect supported
application constructors, select dense/partial-dense/sparse backends, or load a
pretrained checkpoint through the package registry.

## Read First

- Read [application API reference](references/application-api.md) for verified constructor signatures, tensor shapes, architecture options, and output-head behavior.
- Read [pretrained models](references/pretrained-models.md) before using `PretainedRegistry` or a checkpoint-backed API.
- Read [model API troubleshooting](references/troubleshooting.md) for shape assertions, missing compiled ops, sparse backend imports, and invalid architecture/model-name errors.
- Run [pointnet2_forward_smoke.py](scripts/pointnet2_forward_smoke.py) for a CPU-safe dense PointNet2 forward check.
- Run [kpconv_forward_smoke.py](scripts/kpconv_forward_smoke.py) when KPConv/partial-dense compiled ops are relevant.

## Main Workflows

### Choose a high-level constructor

- `PointNet2(...)`: dense point-cloud backbone; good first CPU smoke target.
- `RSConv(...)`: dense/message-style high-level API with `[B, N, C]` inputs.
- `KPConv(...)`: partial-dense model family; requires `torch-points-kernels` and compatible PyG compiled ops.
- `SparseConv3d(..., backend="minkowski"|"torchsparse")`: sparse-convolution API; requires the selected sparse backend.
- `Minkowski(...)`: separate application module that imports `MinkowskiEngine` immediately; do not use unless that optional package imports.

All high-level constructors require `architecture`; valid values are normally
`"unet"`, `"encoder"`, and only when implemented by that factory, `"decoder"`.
Most quick examples use `architecture="unet"`, `input_nc=<feature_channels>`,
`num_layers=<depth>`, and optional `output_nc=<head_channels>`.

### Run a safe PointNet2 smoke

```bash
python sub-skills/model-apis/scripts/pointnet2_forward_smoke.py --num-points 1024 --input-nc 5 --output-nc 10
```

The script builds a synthetic PyG `Batch`, instantiates `PointNet2`, performs a
CPU forward pass, and asserts that the output feature tensor has the requested
head width.

### Run or only inspect a KPConv smoke

```bash
python sub-skills/model-apis/scripts/kpconv_forward_smoke.py --check-imports
python sub-skills/model-apis/scripts/kpconv_forward_smoke.py --run-forward
```

Use the import check first. KPConv relies on compiled kernels; if the target
environment cannot import or run them, route the user to the troubleshooting
reference instead of treating all Torch Points3D workflows as broken.

### Load a pretrained model

Use the registry only when remote downloads and checkpoint side effects are
acceptable:

```python
from torch_points3d.applications.pretrained_api import PretainedRegistry
print(sorted(PretainedRegistry.available_models()))
model = PretainedRegistry.from_pretrained("pointnet2_largemsg-s3dis-1")
```

The class name is misspelled in the public API as `PretainedRegistry`; keep that
spelling in code. See [pretrained models](references/pretrained-models.md) for
`download`, `weight_name`, and `mock_dataset` behavior.

## Boundary Rules

- For dataset class strings, data transforms, `GridSampling3D`, and `Data`/`Batch` layout validation, switch to [datasets-transforms](../datasets-transforms/SKILL.md).
- For Hydra `train.py`/`eval.py`, checkpoints in output folders, W&B/TensorBoard, and forward inference from a saved training run, switch to [training-evaluation](../training-evaluation/SKILL.md).
- For registration descriptors, pair datasets, 3DMatch/KITTI/ETH configs, or FPS registration utility behavior, switch to [registration-workflows](../registration-workflows/SKILL.md).

## Quick Safety Checklist

- Confirm `torch_points3d`, `torch_geometric`, and PyG extension packages import before constructing a model.
- Use dense PointNet2/RSConv for first CPU debugging; postpone sparse models until backend imports pass.
- Keep input shapes consistent with the convolution format: dense APIs expect batch-major `pos` and `x`; KPConv uses PyG geometric batches; sparse models need quantized coordinates.
- Do not run registry downloads or load arbitrary checkpoints without user approval for network and file writes.
