---
name: training-evaluation
description: "Use segmentation_models_pytorch losses, metrics, tensor modes, and
  safe training/evaluation loops for segmentation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-evaluation

Use this sub-skill when an agent needs to train or evaluate segmentation with `segmentation_models_pytorch` (SMP) losses and metrics, diagnose mask/logit shape errors, or adapt a short training loop without downloads or long-running training.

## Use When

- Selecting `DiceLoss`, `JaccardLoss`, `TverskyLoss`, `FocalLoss`, `LovaszLoss`, `SoftBCEWithLogitsLoss`, `SoftCrossEntropyLoss`, or `MCCLoss`.
- Deciding between `BINARY_MODE`, `MULTICLASS_MODE`, and `MULTILABEL_MODE` for logits, masks, losses, and metrics.
- Calling `smp.metrics.get_stats` followed by `iou_score`, `f1_score`, `accuracy`, `precision`, or `recall`.
- Building a minimal PyTorch training/evaluation loop around an SMP model.
- Debugging shape, dtype, threshold, `from_logits`, `ignore_index`, or `class_weights` failures.

## Route Elsewhere

- Choose architectures, `classes`, `in_channels`, decoder options, or `smp.create_model` in [model-building](../model-building/SKILL.md).
- Choose encoder weights and input normalization in [encoders-preprocessing](../encoders-preprocessing/SKILL.md).
- Save, trace, script, ONNX-export, or package trained models in [model-export](../model-export/SKILL.md).

## Core Contract

- Binary segmentation: model output is usually `(N, 1, H, W)` and target masks are `0/1`, preferably `(N, 1, H, W)` for metrics and either `(N, H, W)` or `(N, 1, H, W)` for most losses.
- Multiclass segmentation: model output is `(N, C, H, W)`, target is integer class ids `(N, H, W)`, and classes are mutually exclusive.
- Multilabel segmentation: model output and target are `(N, C, H, W)`, each channel is an independent `0/1` label, and classes may overlap.
- Losses usually consume logits with `from_logits=True`; metrics consume hard integer masks or floating binary/multilabel scores plus a threshold.

## References

- [Losses and metrics](references/losses-and-metrics.md) covers modes, signatures, tensor shapes, reductions, and metric thresholds.
- [Training workflows](references/training-workflows.md) gives compact binary, multiclass, and multilabel loop skeletons.
- [Troubleshooting](references/troubleshooting.md) maps common SMP errors to fixes.
- [validate_training_shapes.py](scripts/validate_training_shapes.py) validates tiny deterministic shape/mode/loss/metric combinations and prints JSON.

## Safe Smoke Check

Run the bundled validator before changing a real loop:

```bash
python sub-skills/training-evaluation/scripts/validate_training_shapes.py --mode binary --batch 2 --classes 1 --height 8 --width 8 --from-logits --metric-threshold 0.5
python sub-skills/training-evaluation/scripts/validate_training_shapes.py --mode multiclass --classes 3 --loss soft-ce
python sub-skills/training-evaluation/scripts/validate_training_shapes.py --mode multilabel --classes 4 --metric-threshold 0.5
```

The helper constructs tiny tensors only; it does not download data, build a model, or train.
