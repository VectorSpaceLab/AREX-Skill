# Customization Troubleshooting

## Registry and Import Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `KeyError: ... is not in the model registry` | Class module was never imported, wrong registry, or wrong default scope | Register with `MODELS`, import the module via `custom_imports`, and initialize `mmdet` scope for standalone builds |
| Custom dataset type not found | Registered in `MODELS` or package import missed | Use `DATASETS.register_module()` and import the dataset module before building dataloaders |
| Custom transform type not found | Transform class not imported or registered in wrong registry | Use `TRANSFORMS.register_module()` and import the module named in `custom_imports` |
| `custom_imports` fails | Import path points to a class, file is not on Python path, or import side effect raises | Import modules only; make the extension package installable/importable; set `allow_failed_imports=False` while debugging |
| Built-in MMDetection type not found in standalone script | Default scope is not `mmdet` or modules not registered | Call `mmdet.utils.register_all_modules()` or initialize the `mmdet` default scope before building |

Use `../scripts/registry_probe.py --registry MODELS --contains MyBBoxHead --imports my_project.models.my_bbox_head` to check import and registry visibility without training.

## Config and Class Mismatch

| Symptom | Likely cause | Fix |
|---|---|---|
| `__init__() got an unexpected keyword argument` | Config keys do not match constructor after inheritance | Inspect the class `__init__`; use `_delete_=True` when replacing an inherited component with incompatible keys |
| Missing `num_classes` or class-count assertion | Dataset `metainfo.classes` and model head class count differ | Set every relevant head `num_classes` to the number of classes and set dataset `metainfo=dict(classes=...)` |
| Loss shape assertion failure | Head outputs, targets, or custom loss reduction contract differ | Match existing loss function signatures and validate shapes with a tiny tensor test |
| Checkpoint load warnings after changing heads | Pretrained checkpoint has old classifier/regressor shapes | Use compatible checkpoint, ignore expected head mismatches, or initialize new heads deliberately |

## Transform and Data Flow Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Later transform raises missing key | Custom transform removed or renamed fields | Trace pipeline keys and preserve required keys until `PackDetInputs` |
| Model receives empty or malformed `DetDataSample` | Transform skipped annotation fields or pack step missing | Ensure bbox labels, masks, ignore flags, and metadata keys match the packer expectations |
| Random filtering drops too many samples | Transform returns `None` unintentionally | Return the results dict unless the transform is designed to filter samples |
| Boxes or masks have wrong type | New transform emits raw arrays where downstream expects `BaseBoxes`, tensors, bitmap masks, or polygons | Follow existing transform outputs and convert consistently before packing |

## Runtime and Optimizer Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Hook never runs | Hook registered but not configured, wrong priority, or method name typo | Add it to `custom_hooks`; use MMEngine hook method names such as `before_train_iter` |
| Hook breaks evaluation/testing | Hook assumes training-only state | Guard by runner mode or implement only stage-specific hook methods |
| Optimizer cannot be built | Custom optimizer registered in wrong node or config is old 2.x style | Register with `OPTIMIZERS`; configure under `optim_wrapper.optimizer` |
| Optimizer constructor parameter error | Custom constructor signature does not match MMEngine constructor contract | Mirror `DefaultOptimWrapperConstructor(optim_wrapper_cfg, paramwise_cfg=None)` style and return an optimizer wrapper |

## Default Scope Problems

If registry builds behave differently in a notebook, script, or test than in `tools/train.py`, suspect scope initialization. MMDetection entrypoints normally set scope from the config. Standalone probes should initialize the `mmdet` scope and register modules before building objects.

## 2.x Migration Pitfalls

- Replace `data.train`, `data.val`, and `data.test` with `train_dataloader`, `val_dataloader`, and `test_dataloader` structures.
- Replace top-level `optimizer` and `lr_config` style runtime with `optim_wrapper` and `param_scheduler`.
- Replace legacy data containers with `DetDataSample`, `InstanceData`, and `PixelData`.
- Replace older registry imports with `mmdet.registry` nodes.
- Recheck method names and signatures of custom detectors/heads; 3.x components commonly separate `loss`, `predict`, and tensor forward behavior.
- Keep full `mmcv` installed when code paths import `mmcv.ops`; `mmcv-lite` can fail with `ModuleNotFoundError: mmcv._ext`.
