# Model Customization Troubleshooting

## Registry `KeyError` or Type Not Found

Symptoms:

- Config build fails with a message that `MyType` is not in a registry.
- `MODELS.get('MyType')` or `METRICS.get('MyMetric')` returns `None`.
- A custom class works in an interactive session but fails from train/test commands.

Checks:

1. Confirm the class uses the right registry decorator, such as `@MODELS.register_module()` for model pieces or `@METRICS.register_module()` for metrics.
2. Confirm the Python module defining the class is imported before config build.
3. For external/project code, add `custom_imports = dict(imports=['my_package.my_module'], allow_failed_imports=False)`.
4. Confirm the package is importable from the launched process, not only from the current shell.
5. Run `scripts/inspect_registry.py --imports my_package.my_module --models MyType`.

Fixes:

- Add missing package `__init__.py` imports for in-tree modules.
- Add or correct `custom_imports` for project/external modules.
- Avoid duplicate class names across packages unless scope is explicit.
- Do not rely on notebook/session side effects for command-line training.

## Missing `custom_imports` or Import Side Effects

MMSegmentation registries populate when modules are imported. Registering code in a file is not enough; the file must be imported.

Good config pattern:

```python
custom_imports = dict(imports=['projects.my_project.models'], allow_failed_imports=False)
default_scope = 'mmseg'
```

Use `allow_failed_imports=False` during development so import errors fail early. If import fails, fix the import path or dependency before editing registry code.

## Default Scope Issues

Symptoms:

- Built-in MMSegmentation modules are not found.
- A type resolves to an unexpected module from another OpenMMLab package.
- A script works after calling `register_all_modules()` but the config command fails.

Checks and fixes:

- Keep `default_scope = 'mmseg'` in normal MMSegmentation configs.
- In standalone scripts, call `from mmseg.utils import register_all_modules; register_all_modules(init_default_scope=True)` before registry inspection/build.
- If composing packages, use explicit scopes and imports rather than changing global defaults accidentally.
- If `register_all_modules` warns that it is forcing scope from another value to `mmseg`, verify that no prior package initialization is hijacking resolution.

## Shape, Channel, or Class Count Mismatch

Common mismatch sources:

- Backbone returns a different number of feature maps than the decode head expects.
- Decode head `in_channels` does not match selected backbone feature channels.
- `in_index` selects the wrong feature level.
- `input_transform='resize_concat'` is configured but `in_channels` is not a sequence or the summed channels are wrong.
- `input_transform='multiple_select'` is configured but the head implementation expects a tensor rather than a list.
- `num_classes`, `out_channels`, dataset classes, and checkpoint head weights disagree.
- Binary segmentation uses `out_channels=1` without checking threshold, label values, or loss type.

Debug path:

1. Build the model without loading a checkpoint if possible.
2. Print or inspect backbone output shapes for a small dummy tensor.
3. Check `decode_head.in_channels`, `decode_head.in_index`, `decode_head.input_transform`, `decode_head.num_classes`, and `decode_head.out_channels`.
4. Run a one-batch forward in `mode='tensor'` before `mode='loss'`.
5. Load checkpoints after the architecture shape is already validated.

## Loss Does Not Backpropagate or Logs Are Missing

Checks:

- Loss dict keys that should be optimized conventionally start with `loss_`.
- Custom loss returns a tensor, not a Python float.
- `ignore_index`, target shape, and `use_sigmoid` match the head output.
- Multiple losses have distinct names if they need separate log entries.
- Mask/depth/binary losses use the target field and tensor shape they expect.

## Optional Project Dependencies

Symptoms:

- Import errors from project modules.
- Built-in model families fail only for specific configs.
- Components import `mmcv.ops`, MMDetection, MMPretrain-era modules, timm, or project-local packages.

Fixes:

- Check the project README and config `custom_imports` first.
- Install optional packages in the runtime environment before model build.
- For selected projects, make the project package importable in the launched process.
- If optional dependencies are not available, switch to a base model zoo config with only core dependencies.

## Checkpoint Conversion or Loading Fails

Symptoms:

- Missing/unexpected keys after loading.
- Tensor shape mismatch for patch embedding, attention QKV, decode head, or class logits.
- Source converter crashes because expected keys such as `state_dict` or `model` are absent.

Debug path:

1. Identify which converter family, if any, matches the source checkpoint.
2. Inspect source checkpoint top-level keys and several sample tensor shapes.
3. Build the target model and inspect target `state_dict()` keys.
4. Convert to a new destination file.
5. Load non-strictly once and record missing/unexpected keys.
6. Reinitialize or drop dataset-specific heads when class count differs.

Do not promise a conversion without source checkpoint access and key/tensor comparison.

## FLOPs Script Fails or Looks Wrong

Known caveats:

- `MaskFormerHead` and `Mask2FormerHead` are explicitly unsupported by `get_flops.py`.
- Optional custom/project modules must be imported before model build.
- Unsupported ops may be omitted or miscounted by the complexity backend.
- The script measures direct model complexity on random input, not end-to-end inference throughput.
- Preprocessing padding can change the reported input shape.

If a model-complexity helper fails because `torch`, `mmengine`, or `mmcv` is unavailable in the current shell, install the normal MMSegmentation runtime dependencies before interpreting the failure as a model bug.

## MMCV Ops Missing

Symptoms:

- Import/runtime error mentioning `mmcv.ops` or missing compiled operators.
- A model works on CPU-only simple configs but fails for heads/backbones using custom CUDA/C++ ops.

Fixes:

- Install an MMCV build compatible with the current PyTorch and CUDA versions.
- Avoid models that require unavailable ops in CPU-only or minimal environments.
- Re-run a tiny import/build check after reinstalling MMCV.

## Quick Diagnostic Commands

List built-ins and custom registrations:

```shell
python skills/mmsegmentation/sub-skills/model-customization/scripts/inspect_registry.py --models EncoderDecoder FCNHead CrossEntropyLoss --metrics IoUMetric
```

Check an external package import side effect:

```shell
python skills/mmsegmentation/sub-skills/model-customization/scripts/inspect_registry.py --imports my_project.models --models MyHead
```

Check project package and optimizer constructor visibility:

```shell
python skills/mmsegmentation/sub-skills/model-customization/scripts/inspect_registry.py --imports my_project.backbones --models MyBackbone --optim-wrapper-constructors LearningRateDecayOptimizerConstructor
```

## Provenance Notes

This troubleshooting guide distills MMSegmentation registry utilities, builder behavior, decode-head validation rules, project-extension examples, model-complexity caveats, and test-backed failure patterns. Treat original repository files as evidence already incorporated here, not as runtime dependencies for the skill.
