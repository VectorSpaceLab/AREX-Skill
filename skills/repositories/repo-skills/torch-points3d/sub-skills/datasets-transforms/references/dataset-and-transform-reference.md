# Dataset and Transform Reference

## Purpose

Read this when resolving Torch Points3D dataset configs, validating transform
chains, writing a new dataset wrapper, or debugging data collation.

## Verified factory APIs

```python
from torch_points3d.datasets.dataset_factory import get_dataset_class, instantiate_dataset
from torch_points3d.datasets.base_dataset import BaseDataset

get_dataset_class(dataset_config)
instantiate_dataset(dataset_config) -> BaseDataset
BaseDataset.create_dataloaders(model, batch_size, shuffle, num_workers, precompute_multi_scale)
BaseDataset.get_num_samples(batch, conv_type)
```

`get_dataset_class` expects `dataset_config.task` and `dataset_config.class`.
The `class` value is split as `<module>.<class_name>` and imported from
`torch_points3d.datasets.<task>.<module>`. The target class is matched
case-insensitively and must subclass `BaseDataset`.

## Data config pattern

A minimal data config contains:

```yaml
# @package data
task: segmentation
class: shapenet.ShapeNetDataset
dataroot: data
pre_transforms:
  - transform: NormalizeScale
  - transform: GridSampling3D
    params:
      size: 0.02
train_transforms:
  - transform: RandomNoise
    params:
      sigma: 0.01
      clip: 0.05
```

The repository snapshot includes task families and configs for:

- `segmentation`: S3DIS, ScanNet, SemanticKITTI, ShapeNet, sparse variants.
- `classification`: ModelNet.
- `object_detection`: ScanNet/VoteNet-style configs.
- `panoptic`: S3DIS and ScanNet sparse/panoptic configs.
- `registration`: 3DMatch fragments/patches, KITTI, ModelNet siamese, ETH, TUM, KAIST, Planetary test sets.

## Transform instantiation

Verified signatures:

```python
instantiate_transform(transform_option, attr="transform")
instantiate_transforms(transform_options)
GridSampling3D(size, quantize_coords=False, mode="mean", verbose=False)
RandomSphere(radius, strategy="random", class_weight_method="sqrt", center=True)
AddFeatByKey(add_to_x, feat_name, input_nc_feat=None, strict=True)
AddFeatsByKeys(list_add_to_x, feat_names, input_nc_feats=None, stricts=None, delete_feats=None)
MultiScaleTransform(strategies)
```

`instantiate_transform` reads attributes using OmegaConf-style access. Pass a
`DictConfig` or `ListConfig`; plain dictionaries can fail because the code uses
`getattr(transform_option, "transform")`.

Lookup order:

1. `torch_points3d.core.data_transform` custom transforms.
2. `torch_geometric.transforms` transforms.
3. Raise `ValueError("Transform <name> is nowhere to be found")`.

## BaseDataset transform behavior

`BaseDataset.set_transform(obj, dataset_opt)` scans config keys containing
`transform` and creates corresponding singular attributes:

- `pre_transforms` -> `pre_transform`
- `train_transforms` -> `train_transform`
- `test_transforms` -> `test_transform`
- `val_transforms` -> `val_transform`

It also creates `inference_transform` by composing `pre_transform` and
`test_transform` when present. Filters work similarly through keys containing
`filter`.

## Collate and convolution formats

`BaseDataset._get_collate_function` chooses a collate function from the model's
`conv_type` and `precompute_multi_scale` flag:

| Conv type family | Collate behavior | Notes |
| --- | --- | --- |
| Dense | `SimpleBatch.from_data_list` | Fixed-size samples; dense application APIs use batch-major tensors. |
| Non-dense PyG | `torch_geometric.data.Batch.from_data_list` | Variable-size point clouds and a `batch` vector. |
| Partial dense + multiscale | `MultiScaleBatch.from_data_list` | Only supported when `conv_type.lower() == "partial_dense"`. |
| Other conv type + multiscale | Raises `NotImplementedError` | Disable `precompute_multi_scale` or choose a compatible model. |

## Feature transform cautions

`AddFeatByKey` and `AddFeatsByKeys` concatenate attributes into `data.x` only
when the `add_to_x` flag is true. With `strict=True`, missing feature keys or
unexpected feature dimensions raise errors; with `strict=False`, missing keys
can be tolerated. Validate feature names and `input_nc_feat` when a model sees
channel mismatches.

## Dataset addition checklist

When adding a dataset to a checkout:

1. Pick the task family and module name.
2. Subclass `BaseDataset` and set `train_dataset`, `test_dataset`, and optionally `val_dataset`.
3. Implement `get_tracker(wandb_log: bool, tensorboard_log: bool)`.
4. Provide dataset properties used by model configs: commonly `num_classes`, `feature_dimension`, class weights, category mappings, or registration-specific dimensions.
5. Add a data config with `task`, `class`, `dataroot`, transforms, and optional filters.
6. Use `get_dataset_class` or the bundled transform smoke helper before launching preprocessing/downloads.
