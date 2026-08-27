# Configuration Reference

## Purpose

Read this when you need to understand how Open3D-ML config files are loaded,
merged, and turned into model/dataset/pipeline objects.

## Verified API facts

From installed-package inspection:

- `Config.load_from_file(filename)` loads YAML or Python config files.
- `Config.merge_cfg_file(cfg, args, extra_dict)` merges CLI-style overrides into
  an existing combined config.
- `get_module(module_type, module_name, framework=None)` resolves registered
  datasets, models, or pipelines.
- `convert_framework_name(framework)` normalizes framework strings to `tf` or
  `torch`.
- `convert_device_name(device_type, device_ids)` normalizes `cpu` or `cuda`
  device names plus integer IDs.

## Config anatomy

The common combined config shape has three top-level sections:

- `dataset`
- `model`
- `pipeline`

Each section usually includes a `name` key plus section-specific parameters.

## Merge behavior

The config loader and merge helpers support a few useful patterns:

- CLI-style overrides can update `dataset_path`, `split`, `device`, `ckpt_path`,
  and extra dotted keys.
- Nested dictionaries are merged recursively.
- String-like numeric and boolean values may be normalized by the merge helper.
- Framework-specific model and pipeline names are resolved through the registry.

## Practical config rules

- Keep config files close to the workflow they drive.
- Make sure the `name` in each section matches a registered class.
- Use `dataset_path` only for the dataset section.
- Use `ckpt_path` in the model section when you want to load a checkpoint.
- Set `device` consistently in the pipeline and model when you are using a
  direct API workflow.

## Common config file names in this repo

The repository ships configs such as:

- `randlanet_semantickitti.yml`
- `pointpillars_kitti.yml`
- `kpconv_s3dis.yml`
- `sparseconvunet_scannet.yml`
- `pointtransformer_s3dis.yml`

Use these as templates when you need a known-good structure.

## Example pattern

```python
from open3d.ml.utils import Config, get_module
import open3d.ml.torch as ml3d

cfg = Config.load_from_file("path/to/config.yml")
Dataset = get_module("dataset", cfg.dataset.name)
Model = get_module("model", cfg.model.name, "torch")
Pipeline = get_module("pipeline", cfg.pipeline.name, "torch")
```

## Troubleshooting tie-in

If config loading fails, first check:

- the file path
- the `name` fields in `dataset`, `model`, and `pipeline`
- the framework string used for `get_module`
- whether the required backend is actually available
