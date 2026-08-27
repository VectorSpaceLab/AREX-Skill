# Troubleshooting Extensions and Projects

Use this guide to isolate extension failures before running expensive training or project scripts.

## Registry Lookup Fails

Symptoms:

- `KeyError` or registry error for a name such as `ToyBackbone`, `PointRendMaskHead`, or a custom ROI heads class.
- `build_model`, `build_backbone`, or `build_roi_heads` cannot find the configured component.

Checks:

1. Import the module that contains the `@REGISTRY.register()` decorator before building anything.
2. Confirm the config value exactly matches the registered class/function name or explicit registered name.
3. Confirm the class was registered in the correct registry, such as `BACKBONE_REGISTRY` versus `ROI_HEADS_REGISTRY`.
4. Query the registry directly with `REGISTRY.get("Name")` in a small script.
5. Run `python scripts/registry_smoke_check.py` from this sub-skill to rule out a broken base registry installation.

Common cause: defining a custom class in a file but never importing that file in the process that loads the config.

## Project Config Merge Fails

Symptoms:

- Unknown config keys such as `MODEL.POINT_HEAD`, `MODEL.INS_EMBED_HEAD`, `SOLVER.POLY_LR_POWER`, or project-specific input settings.
- A PointRend, DeepLab, or Panoptic-DeepLab YAML fails before model construction.

Checks:

1. Start from `get_cfg()`.
2. Import the project package.
3. Call the project config adder before `cfg.merge_from_file` or `cfg.merge_from_list`.
4. Use the correct adder: `add_pointrend_config`, `add_deeplab_config`, or `add_panoptic_deeplab_config`.
5. For Panoptic-DeepLab, use its own adder; it adds DeepLab settings first and then panoptic-specific settings.

A PointRend failure is often fixed by:

```python
from detectron2.config import get_cfg
from detectron2.projects.point_rend import add_pointrend_config

cfg = get_cfg()
add_pointrend_config(cfg)
cfg.merge_from_file("project_config.yaml")
```

## Wrong Registry Name

Detectron2 uses multiple registries with similar construction signatures. A class registered in one registry is invisible to another. For example, a custom backbone must be in `BACKBONE_REGISTRY` and selected by `cfg.MODEL.BACKBONE.NAME`; an ROI heads class must be in `ROI_HEADS_REGISTRY` and selected by `cfg.MODEL.ROI_HEADS.NAME`.

When in doubt, identify the builder that fails and read the config key it uses. Then check that exact registry.

## `ShapeSpec` or Feature Name Mismatch

Symptoms:

- Channel mismatch, missing feature-map key, ROI pooler errors, mask-head shape errors, FPN/RPN shape errors, or semantic-head tensor mismatches.

Checks:

1. Inspect `backbone.output_shape()`.
2. Confirm every configured `IN_FEATURES` list uses keys returned by `output_shape()`.
3. Confirm each returned `ShapeSpec` has correct `channels` and `stride` values.
4. For project heads, confirm project config adders did not change default feature lists in a way that conflicts with the custom backbone.
5. Build and test the smallest component first: backbone, then proposal generator or heads, then full model.

A toy backbone that returns `{"toy": ShapeSpec(channels=64, stride=16)}` cannot be consumed by config values that still expect `p2`, `p3`, `p4`, or `p5` unless you change downstream `IN_FEATURES` or provide those feature names.

## Custom Task Missing Data or Metadata Changes

Symptoms:

- Model builds but training fails on missing `Instances` fields, `sem_seg`, keypoints, masks, category metadata, evaluator tasks, or mapper outputs.

Checks:

1. List every new field consumed by the model or loss.
2. Update dataset registration and mapper output to provide those fields.
3. Update metadata such as class names, keypoint names, evaluator type, or label divisors when evaluators/post-processing need it.
4. Override `DefaultTrainer.build_train_loader`, `build_test_loader`, or `build_evaluator` if defaults no longer match the task.

A registry change only wires model construction. It does not update data loading or evaluation semantics.

## Optional Project Dependency or Build Failure

Symptoms:

- Import failures for optional research projects.
- CUDA/C++ extension issues, missing third-party packages, Cityscapes/panoptic APIs, DensePose dependencies, or project-specific dataset tooling failures.

Checks:

1. Confirm whether the requested project is one of the installed package mappings or merely a repository example.
2. Try importing only the needed project module before installing anything broad.
3. Install the smallest explicit dependency set required by that project and task.
4. Do not install `all` or development extras just because a project import failed; identify the missing package first.
5. Treat original project train/apply scripts as reference patterns unless the user explicitly wants to run that project and has prepared data and dependencies.

Research projects may not have the same support or stability level as core Detectron2 APIs.

## `@configurable` Misuse

Symptoms:

- `Class with @configurable must have a 'from_config' classmethod`.
- `from_config must take 'cfg' as the first argument`.
- Explicit overrides silently do not behave as expected.

Checks:

1. Put `@configurable` on `__init__` for classes.
2. Define `@classmethod from_config(cls, cfg, ...)` with `cfg` first.
3. Return a dictionary of explicit constructor arguments.
4. Use keyword-only constructor arguments for clarity.
5. Test both explicit construction and config construction separately.

## Diagnose Before Heavy Work

Preferred order:

1. Run the bundled registry smoke script.
2. Import custom/project modules in a tiny Python process.
3. Query the relevant registry directly.
4. Add project config keys and merge the config.
5. Build the smallest component.
6. Build the full model.
7. Only then move to data loading, training, evaluation, or project scripts.
