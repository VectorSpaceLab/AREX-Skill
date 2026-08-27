# MMDetection3D Config Operating Reference

This reference distills MMDetection3D v1.x config behavior for selecting and adapting existing configs. It is for config reasoning only; route actual dataset conversion to `data-preparation`, training/testing commands to `training-evaluation`, and custom Python components to `customization-extensions`.

## Mental model

MMDetection3D configs are Python files consumed by MMEngine's config system. A usable v1.x config is normally assembled from four base categories plus method-specific overrides:

| Area | Common top-level keys | What to inspect |
| --- | --- | --- |
| Model | `model` | Detector/segmentor type, preprocessor, voxelization, backbones/necks, heads, class counts, `train_cfg`, `test_cfg`. |
| Data | `train_dataloader`, `val_dataloader`, `test_dataloader` | Dataset type, `data_root`, `ann_file`, `data_prefix`, `metainfo`, pipeline, batch size, sampler, workers. |
| Evaluation | `val_evaluator`, `test_evaluator` | Metric type, annotation file, metric mode, submission/result prefixes, `format_only`. |
| Training loop | `train_cfg`, `val_cfg`, `test_cfg` | Loop type, max epochs/iters, validation interval. |
| Optimization | `optim_wrapper`, `param_scheduler`, `auto_scale_lr` | Optimizer, AMP wrapper, gradient clipping, LR/momentum schedules, automatic LR scaling. |
| Runtime | `default_scope`, `default_hooks`, `custom_hooks`, `env_cfg`, `visualizer`, `log_processor`, `load_from`, `resume`, `work_dir` | Registry scope, logging/checkpoint hooks, distributed backend, visualization backend, checkpoint/resume behavior. |

The registry scope should normally be `mmdet3d`. MMDetection3D's registries inherit from MMEngine registries and register datasets, transforms, models, metrics, visualizers, inferencers, hooks, optimizers, schedulers, loops, and task utilities under package locations. If a config references another OpenMMLab scope, keep the scope prefix explicit, for example `mmdet.FocalLoss`.

## Inheritance rules that matter

- `_base_` may be one file or a list of files. Primitive method configs usually combine a model base, dataset base, schedule base, and default runtime base.
- Method folders usually keep one primitive config and derive variants from it. A child config can inherit another method config and override only changed fields.
- Inherited dictionaries merge recursively. When replacing a subtree whose constructor uses incompatible keywords, set `_delete_=True` in that subtree.
- Intermediate variables such as `train_pipeline`, `test_pipeline`, `class_names`, `point_cloud_range`, `input_modality`, and `backend_args` are not magic after override. If you redefine them in a child config, pass them again into the dataloader/model/evaluator fields that consume them.
- `{{_base_.name}}` reuses a variable from the base config. Use it when a child config needs a base object as a starting point without duplicating the whole base.
- If `_base_` cannot be resolved, inspect from the directory that contains the config or use a path whose relative bases are present.

## Config naming convention

Config names encode enough information to choose a family before opening the file:

```text
{algorithm}_{components}_{training-settings}_{train-dataset}_{optional-test-dataset}.py
```

Common tokens:

- Algorithm/model family: `pointpillars`, `centerpoint`, `second`, `votenet`, `fcos3d`, `minkunet`, `cylinder3d`, and similar.
- Components: voxel/pillar size, backbone, neck, head options, DCN, circle NMS, backend name, or feature width.
- Training settings: GPU x batch notation such as `8xb4`, schedule such as `2x`, `3x`, `20e`, `80e`, `160e`, AMP, TTA, or augmentation notes.
- Dataset/task: `kitti-3d-car`, `kitti-3d-3class`, `nus-3d`, `waymoD5-3d-car`, `scannet-seg`, `s3dis-seg`, `semantickitti`, `nuim`, and related dataset tokens.

Treat a checkpoint basename as compatible with a config only when the algorithm, component, schedule, dataset, and class-count tokens line up. Download path versions may be older than the repo/package version, so compare names and config semantics rather than relying only on URL version text.

## Inspect before editing

Use the bundled inspector:

```bash
python sub-skills/configuration-model-zoo/scripts/check_config.py configs/pointpillars/example_config.py
```

The script parses with MMEngine when installed, applies optional `--cfg-options`, and summarizes model, dataloader, evaluator, loop, optimization, and runtime keys. Use it to discover the real key path before writing overrides.

Recommended inspection checklist:

1. Confirm `default_scope`, model `type`, and whether components use plain MMDetection3D names or scope-prefixed OpenMMLab names.
2. Check `data_preprocessor` and voxelization settings before changing `point_cloud_range`, `voxel_size`, or point dimensions.
3. Check all train/val/test dataset wrappers. A training dataset may be wrapped in `RepeatDataset`, `CBGSDataset`, or a concatenation wrapper.
4. Check that `metainfo.classes`, model head `num_classes`, evaluator annotation files, and dataset `ann_file` agree.
5. Check whether AMP is expressed through `AmpOptimWrapper` or command-line flags owned by the training workflow.
6. Check `test_pipeline`, `test_cfg`, and evaluator fields before enabling TTA, result formatting, or submission outputs.

## Safe adaptation patterns

### Create a child config

Prefer a child config for changes that should be reproducible:

```python
_base_ = "./base_method_config.py"

work_dir = "./work_dirs/my_experiment"

data_root = "data/my_dataset/"
class_names = ["Car", "Pedestrian"]
metainfo = dict(classes=class_names)

train_dataloader = dict(
    dataset=dict(
        data_root=data_root,
        ann_file="my_infos_train.pkl",
        metainfo=metainfo))
val_dataloader = dict(
    dataset=dict(
        data_root=data_root,
        ann_file="my_infos_val.pkl",
        metainfo=metainfo))
test_dataloader = val_dataloader
```

Then re-inspect the child config. If the base dataset is wrapped, override the inner `dataset` object rather than assuming the dataset is at `train_dataloader.dataset`.

### Use `_delete_=True` for incompatible replacements

Use `_delete_=True` when changing a component type whose constructor arguments differ from the inherited component:

```python
model = dict(
    pts_neck=dict(
        _delete_=True,
        type="SECONDFPN",
        in_channels=[64, 128, 256],
        upsample_strides=[1, 2, 4],
        out_channels=[128, 128, 128]))
```

Without `_delete_=True`, inherited keys from the old component may remain and cause constructor errors later.

### Use `--cfg-options` for one-off runs

For train/test command handoff, small in-place overrides can be passed as `--cfg-options`:

```bash
--cfg-options model.backbone.norm_eval=False
--cfg-options train_dataloader.batch_size=2
--cfg-options work_dir=./work_dirs/debug_run
--cfg-options model.data_preprocessor.mean="[127,127,127]"
```

Rules:

- Use dotted dictionary paths in the parsed config, not guessed legacy paths.
- Use numeric list indexes for list elements, such as `train_dataloader.dataset.pipeline.0.type=LoadPointsFromFile`.
- Quote list/tuple values without whitespace if passing through a shell.
- Prefer a child config when overrides touch pipelines, dataset wrappers, class names, or multiple coordinated fields.

## Changing datasets or classes

Changing only `data_root` is safe when the converted dataset layout and annotation format are identical. For a real dataset or class change, update all coupled fields:

- Dataset `data_root`, `ann_file`, `data_prefix`, `metainfo`, and `box_type_3d`.
- Train/test pipelines, especially point dimensions, sweeps, image loading, object sampling database, range filters, and packing keys.
- Model head `num_classes`, anchor/coder class settings, class-specific sample groups, and any class-order assumptions.
- Evaluator `ann_file`, metric type, `format_only`, and submission/result prefix.
- Geometry-sensitive values such as `point_cloud_range`, voxel size, anchor ranges, BEV output shape, and preprocessor voxel layer.

If the raw data has not already been converted into MMDetection3D-compatible info files, stop and route to `data-preparation` before promising that the config will run.

## Legacy compatibility clues

Older configs may use fields that are converted by compatibility helpers:

- `total_epochs` can be converted into an epoch runner max-epoch setting.
- Old `data.samples_per_gpu`, `data.workers_per_gpu`, and `data.persistent_workers` are migrated into dataloader settings.
- `imgs_per_gpu` is deprecated in favor of `samples_per_gpu` in old-style config blocks.
- Do not set the old global loader key and the new per-dataloader key at the same time; compatibility tests assert that this is invalid.

For v1.x configs, prefer the explicit top-level `train_dataloader`, `val_dataloader`, and `test_dataloader` keys.
