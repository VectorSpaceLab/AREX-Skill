# Dataset and Transform Troubleshooting

## Dataset class not found

**Symptoms**

- `NotImplementedError` says the module should contain a subclass of `BaseDataset` whose name matches the config.
- `ModuleNotFoundError` for `torch_points3d.datasets.<task>.<module>`.
- Config has a `class` value but dataset factory cannot resolve it.

**Recovery**

1. Check that the data config has `task`, `class`, and `dataroot`.
2. Ensure `class` is `<module>.<ClassName>` without the task prefix. Example: `shapenet.ShapeNetDataset` with `task: segmentation` resolves to `torch_points3d.datasets.segmentation.shapenet.ShapeNetDataset`.
3. Verify the class subclasses `BaseDataset` and the module import does not fail for unrelated missing dependencies.
4. Run:

```bash
python sub-skills/datasets-transforms/scripts/transform_config_smoke.py --data-config path/to/data.yaml --expect-class ShapeNetDataset
```

## Transform name is invalid

**Symptoms**

- `ValueError: Transform <name> is nowhere to be found`.
- Plain dictionaries passed to `instantiate_transform` fail with `TypeError: getattr(): attribute name must be string`.

**Recovery**

Use exact transform class names and pass OmegaConf containers:

```python
from omegaconf import OmegaConf
from torch_points3d.core.data_transform import instantiate_transform
cfg = OmegaConf.create({"transform": "GridSampling3D", "params": {"size": 0.1}})
transform = instantiate_transform(cfg)
```

If the transform belongs to PyG, verify the PyG version still exposes that class
under `torch_geometric.transforms`.

## Feature transform strictness failure

**Symptoms**

- `AddFeatByKey` errors on a missing attribute.
- Feature channel count becomes larger or smaller than `input_nc`.

**Recovery**

Check `feat_name`, `add_to_x`, `input_nc_feat`, and `strict`. Use
`strict=False` only when missing optional features are expected. After applying
feature transforms, assert `data.x.shape[-1]` matches the model's `input_nc`.

## Multiscale preprocessing unsupported

**Symptoms**

- `NotImplementedError: MultiscaleTransform is activated and supported only for partial_dense format`.
- KPConv runs faster with precompute but another model crashes.

**Recovery**

Enable `training.precompute_multi_scale=True` only for partial-dense/KPConv
workflows. Disable it for dense PointNet2/RSConv and generic PyG message-passing
models unless the model explicitly advertises compatible strategies.

## Dataset constructor starts downloads or heavy preprocessing

**Symptoms**

- The command prompts for dataset terms or starts a large download.
- PyG creates large `processed/` directories.
- ScanNet/S3DIS/KITTI paths fail with missing files.

**Recovery**

Stop and obtain user approval for downloads, license gates, and destination.
Use the layout reference and safe scripts first:

```bash
python sub-skills/datasets-transforms/scripts/check_scannet_layout.py --base-dir /path/to/scans
python sub-skills/datasets-transforms/scripts/transform_config_smoke.py --transforms-yaml '[{"transform":"GridSampling3D","params":{"size":0.1}}]'
```

## Dense versus PyG batch confusion

**Symptoms**

- Dense application APIs assert on `data.pos.shape`.
- KPConv or registration code receives dense `[B, N, C]` data and fails.

**Recovery**

Route dense PointNet2/RSConv standalone usage to [model-apis](../../model-apis/SKILL.md). For dataset factory or `Trainer` workflows, let the dataset and model `conv_type` choose the collate function through `BaseDataset.create_dataloaders`.
