---
name: config-customization
description: "Choose, customize, and validate MMYOLO model-family configs
  without running training, testing, deployment, or dataset conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# MMYOLO Config Customization

Use this sub-skill when the task is to choose an MMYOLO configuration, understand MMEngine inheritance, edit model/dataset/runtime fields, apply safe `--cfg-options`, or preflight a config before handing it to training, testing, inference, or deployment workflows.

## Read this way

1. Start with [model zoo and config selection](references/model-zoo-and-configs.md) to choose a family and baseline config pattern.
2. Use [configuration editing](references/configuration.md) for `_base_` inheritance, one-class COCO-style fine-tuning edits, `num_classes`, dataloaders, evaluators, hooks, schedulers, `--cfg-options`, TTA, and `batch_shapes_cfg` caveats.
3. Use [troubleshooting](references/troubleshooting.md) when config loading, class metadata, TTA, or override behavior is wrong.
4. Run [`scripts/print_mmyolo_config_summary.py`](scripts/print_mmyolo_config_summary.py) against a user-provided config to print a model/dataloader/runtime/TTA summary without training or building a runner.

## Scope and routing

This sub-skill owns:

- Config families for YOLOv5, YOLOv6, YOLOv7, YOLOv8, YOLOX, RTMDet, and PPYOLOE.
- `model-index.yml` and family `metafile.yml` selection signals distilled into model-family guidance.
- MMEngine `_base_` inheritance, `_delete_=True`, inherited variable reuse, intermediate-variable rebinding, and config filename interpretation.
- Key config fields: `model`, `train_dataloader`, `val_dataloader`, `test_dataloader`, `val_evaluator`, `test_evaluator`, `train_cfg`, `default_hooks`, `custom_hooks`, `optim_wrapper`, `param_scheduler`, `load_from`, `resume`, `visualizer`, `log_processor`, and `env_cfg`.
- Custom dataset metadata: lowercase `metainfo` keys, `classes`, `palette`, `num_classes`, evaluator annotation files, batch size/workers, validation/checkpoint/logger intervals, and scheduler adjustments.
- Config-only TTA checks: `tta_model`, `tta_pipeline`, and the `batch_shapes_cfg` incompatibility handled by MMYOLO test logic.

Route elsewhere:

- Training, testing, evaluation command execution, checkpoint handling, metrics output, and distributed launch: `training-evaluation`.
- Dataset conversion, COCO/YOLO layout validation, annotation inspection, anchor optimization, and data browsing: `data-tools`.
- Low-level registry/class/API extension, custom modules, and model component implementation: `model-api`.
- ONNX/TensorRT/RKNN/DeepStream/export/deploy configs and backend artifacts: `deployment-conversion`.

## Fast decision checklist

- **Need a baseline model?** Pick a family by speed/accuracy/resource signals, then choose the nearest size/config pattern in [model zoo and config selection](references/model-zoo-and-configs.md).
- **Need to fine-tune on one or a few COCO-style classes?** Create a small child config inheriting the closest baseline. Do not edit the baseline in-place unless the user explicitly wants to maintain that project config.
- **Need a quick override?** Use `--cfg-options` only for scalar, simple dict, or simple list changes; prefer a child config for dataset, pipeline, model-head, scheduler, hook, or TTA edits.
- **Need to validate before a run?** Use the bundled summary helper and inspect `num_classes`, metainfo, annotation paths, dataloader batch size/workers, evaluator files, epoch/interval settings, and TTA readiness.
