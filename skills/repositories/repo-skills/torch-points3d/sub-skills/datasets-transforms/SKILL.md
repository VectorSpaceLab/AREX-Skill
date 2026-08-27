---
name: datasets-transforms
description: "Use Torch Points3D dataset factories, point-cloud data layouts,
  transforms, filters, collate modes, and safe dataset preflight helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Torch Points3D Datasets and Transforms

Use this sub-skill when the user asks about Torch Points3D data configs,
`torch_geometric.data.Data` fields, dataset class resolution, transform/filter
YAML, collate behavior, data layout preflights, or adding a dataset to the
framework.

## Read First

- Read [dataset and transform reference](references/dataset-and-transform-reference.md) for factory signatures, config fields, collate modes, and common transform patterns.
- Read [data layouts](references/data-layouts.md) for ShapeNet, S3DIS, ScanNet, ModelNet, SemanticKITTI, object detection, panoptic, and registration data expectations.
- Read [dataset/transform troubleshooting](references/troubleshooting.md) for class lookup failures, invalid transform names, missing features, multiscale constraints, and download/layout blocks.
- Run [transform_config_smoke.py](scripts/transform_config_smoke.py) to validate an OmegaConf-style transform or data-config class lookup without training.
- Run [check_scannet_layout.py](scripts/check_scannet_layout.py) to inspect a ScanNet raw scene directory without downloading missing files.

## Main Workflows

### Resolve a dataset class from config

Torch Points3D dataset configs use two required selectors:

```yaml
task: segmentation
class: shapenet.ShapeNetDataset
dataroot: data
```

The factory imports `torch_points3d.datasets.<task>.<module>` and searches for a
case-insensitive subclass of `BaseDataset` matching the class name. Use the
transform smoke helper with `--data-config` to check class resolution before
instantiating datasets that may download or preprocess data.

### Validate transform YAML

Transforms are OmegaConf objects with a `transform` name plus optional `params`
and `lparams`:

```yaml
- transform: GridSampling3D
  params:
    size: 0.1
- transform: Center
```

Torch Points3D first looks in `torch_points3d.core.data_transform`, then in
`torch_geometric.transforms`. Use:

```bash
python sub-skills/datasets-transforms/scripts/transform_config_smoke.py \
  --transforms-yaml '[{"transform":"GridSampling3D","params":{"size":0.1}},{"transform":"Center"}]'
```

### Choose a point-cloud data format

- Dense format: fixed-size tensors collated into `[B, N, C]`; used by dense APIs such as PointNet2 and RSConv.
- PyG sparse/message-passing format: variable-size point clouds concatenated with a `batch` vector; used by many PyG and registration utilities.
- Partial-dense format: KPConv-style fixed neighbor slots; supports `precompute_multi_scale` only for `PARTIAL_DENSE` models.
- Sparse convolution format: quantized coordinates/features for MinkowskiEngine or torchsparse backends.

### Add or adapt a dataset

Follow the framework convention: create a `BaseDataset` subclass under the task
family (`segmentation`, `classification`, `registration`, `object_detection`, or
`panoptic`), define train/test/val dataset attributes, and implement
`get_tracker`. Then create a matching data config with `task`, `class`,
`dataroot`, and transforms.

## Boundary Rules

- For model constructor choices and forward smoke tests, use [model-apis](../model-apis/SKILL.md).
- For train/eval commands, checkpoints, logging, and config composition across `task`/`models`/`data`/`model_name`, use [training-evaluation](../training-evaluation/SKILL.md).
- For registration-specific pair data, descriptor outputs, FPS utility behavior, and 3DMatch/KITTI/ETH evaluation, use [registration-workflows](../registration-workflows/SKILL.md).

## Safety Checklist

- Do not instantiate large dataset classes until data size, license, credentials, and preprocessing side effects are acceptable.
- Use config/class/transform smoke checks before `Trainer` setup.
- Keep transform names exact and pass OmegaConf containers rather than plain dictionaries to `instantiate_transform`.
- When `precompute_multi_scale=True`, confirm the model convolution type is `PARTIAL_DENSE`; other conv types raise `NotImplementedError`.
