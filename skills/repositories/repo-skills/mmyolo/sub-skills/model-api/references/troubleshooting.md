# Model API troubleshooting

Use this guide for MMYOLO registry, model-extension, plugin, preprocessor, and deploy-mode failures.

## Registry lookup fails

Symptoms:

```text
KeyError: 'DummyBackbone is not in the model registry'
Failed to import custom modules
Cannot find registry scope mmyolo
```

Checks:

1. In standalone code, call `register_all_modules()` before `MODELS.build`, `DATASETS.build`, `TRANSFORMS.build`, or `TASK_UTILS.build`.
2. Ensure the custom module is imported before build. Use `custom_imports = dict(imports=['my_project'], allow_failed_imports=False)` in config-driven flows.
3. Use the right registry: detectors/backbones/necks/heads/losses/preprocessors/plugins go to `MODELS`; transforms go to `TRANSFORMS`; coders/assigners go to `TASK_UTILS`; visualizers go to `VISUALIZERS`.
4. If using a parent OpenMMLab package, use a prefix such as `mmdet.ResNet` and import that package's models first when needed.
5. Run the bundled inspection helper:

```bash
python scripts/inspect_mmyolo_registry.py --registry MODELS --contains Dummy --custom-import my_project
```

If the name still does not appear, the decorator did not run or the package import failed.

## Default scope warnings or wrong registry owner

Symptom:

```text
The current default scope "..." is not "mmyolo"; register_all_modules will force the current default scope to be "mmyolo".
```

Meaning: another MMEngine default scope was active. In short standalone scripts this warning is often acceptable; MMYOLO creates a `mmyolo` scope so unprefixed types resolve as MMYOLO types.

Safer choices:

- Use `register_all_modules(init_default_scope=False)` when you only need registration side effects and the caller intentionally controls scope.
- Prefix external types (`mmdet.*`, `mmcls.*`, etc.) instead of relying on the current default scope.
- Avoid changing the global default scope from import-time code inside reusable project packages.

## Custom import fails

Symptoms:

```text
ModuleNotFoundError: No module named 'my_project'
ImportError while loading custom_imports
```

Checks:

- The project package must be installed or visible on `PYTHONPATH`.
- The import string should name a package/module, not a file path.
- `__init__.py` should import the classes whose decorators need to run.
- Avoid import-time training, checkpoint loading, dataset reads, or GPU probes; a registry module should register classes cheaply.

## Backbone replacement shape mismatch

Common symptoms:

```text
AssertionError in neck forward: len(inputs) != len(in_channels)
RuntimeError: expected input to have N channels, but got M
```

Likely cause: the replacement backbone outputs do not match the existing neck/head settings.

Fix checklist:

- Determine the replacement backbone output scales and channels.
- Set `neck.in_channels` to those channel values.
- Set `neck.out_channels` and `bbox_head.head_module.in_channels` consistently.
- Update `out_indices` when the external backbone indexes stages differently.
- Use `_delete_=True` when replacing an inherited backbone subtree that still contains incompatible keys.

## Plugin insertion errors

Symptoms:

```text
AssertionError: len(stages) == self.num_stages
TypeError: __init__() got an unexpected keyword argument 'in_channels'
KeyError for plugin type
```

Fix checklist:

- Ensure `stages` length matches the backbone's number of stages.
- Ensure each plugin dict has a `cfg` key.
- Use a plugin class compatible with MMEngine/MMCV plugin construction; MMYOLO passes stage channel information to the plugin builder.
- Prefix or import plugin owners when the plugin is from a parent registry.
- For MMYOLO `CBAM`, make sure MMYOLO model registrations have been loaded.

## Dense head or loss config mismatch

Symptoms:

```text
unexpected keyword argument
missing required positional argument: head_module
loss/coder type not found
shape mismatch between feature levels and head module
```

Fix checklist:

- MMYOLO heads often require a nested `head_module=dict(...)`; do not flatten head-module keys into the wrapper head.
- Keep `num_classes`, `in_channels`, `num_base_priors`, and `featmap_strides` aligned with the model family.
- Use `mmdet.` prefixes for MMDetection losses/generators/coders when the class is owned by MMDetection.
- Put coders/assigners under the expected fields (`bbox_coder`, `train_cfg=dict(assigner=...)`) rather than registering them as arbitrary model submodules.

## Data preprocessor and collate mismatch

Symptoms:

```text
"inputs" should be a list of Tensor
"data_samples" should be a dict
KeyError: bboxes_labels
```

Likely cause: the selected preprocessor expects MMYOLO's YOLO-style collate output.

Fix checklist:

- Use `YOLOv5DetDataPreprocessor` with MMYOLO's YOLOv5-style collate in training.
- Use `PPYOLOEDetDataPreprocessor` only with its expected list-input training format.
- Keep batch augmentation components paired with preprocessors that understand their data structure.
- Route full dataloader and transform pipeline debugging to `data-tools` or `config-customization`.

## `switch_to_deploy` changes nothing

Symptoms:

```text
Switch model to deploy modality.
```

but model structure appears unchanged.

Meaning: `switch_to_deploy(model)` only mutates modules that are instances of MMYOLO `RepVGGBlock`. If none are present, it effectively does nothing besides printing.

Check:

```python
from mmyolo.models import RepVGGBlock
print(sum(isinstance(m, RepVGGBlock) for m in model.modules()))
```

If the count is zero, do not force deploy conversion. Route export or inference concerns to the appropriate sub-skill.

## `switch_to_deploy` called too early

Problem: after conversion, `RepVGGBlock` training-time branches are fused and removed. Continuing training on the same object is not the intended use.

Safer pattern:

1. Train or load weights into a normal model instance.
2. Save/checkpoint or keep the training model separate.
3. Create/load a second model object for inference/export.
4. Call `model.eval()` and then `switch_to_deploy(model)` on that second object.

## Inspection helper cannot import MMYOLO

Symptoms:

```text
Failed to import/register MMYOLO
No module named 'mmyolo'
No module named 'mmcv' / 'mmdet' / 'mmengine'
```

Fix checklist:

- Install MMYOLO and its OpenMMLab core dependencies in the active Python environment.
- Confirm `python -c "import mmyolo; print(mmyolo.__version__)"` works.
- If using an editable checkout or a project-local extension, ensure the package is visible to the same Python executable that runs the helper.
- Do not treat optional packages needed by deployment, large-image inference, or visualization as required for registry inspection unless your custom module imports them at module import time.

## Avoid over-broad fixes

Do not solve a registry/API issue by launching training, downloading checkpoints, or running dataset conversion. Registry presence, constructor signatures, and default-scope behavior can be checked with imports, config parsing, and the bundled inspection helper.
