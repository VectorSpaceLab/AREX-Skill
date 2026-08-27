---
name: segmentation-models-pytorch
description: "Route segmentation_models_pytorch tasks for semantic segmentation
  model creation, encoders, preprocessing, losses, metrics, export, and
  repository maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Segmentation Models PyTorch

Use this repo skill when the task involves `segmentation_models_pytorch` (SMP), a PyTorch semantic segmentation library with high-level model constructors, pretrained encoders, segmentation losses/metrics, and save/load/export workflows.

## Start Here

- Read [Package Overview](references/package-overview.md) for the public API surfaces, dependency expectations, and how the sub-skills fit together.
- Read [Repository Provenance](references/repo-provenance.md) before deciding whether this skill is current for a checkout or package version.
- Read [Troubleshooting](references/troubleshooting.md) for cross-cutting install/import, PyTorch, Hugging Face Hub, optional dependency, and routing failures.
- Run [check_install.py](scripts/check_install.py) when an environment may not have SMP, PyTorch, timm, Hugging Face Hub, or CUDA visibility set up correctly.

## Route By Task

- Use [model-building](sub-skills/model-building/SKILL.md) to create or debug `Unet`, `FPN`, `DeepLabV3Plus`, `Segformer`, `DPT`, `smp.create_model`, tensor shapes, auxiliary heads, or encoder freeze/unfreeze behavior.
- Use [encoders-preprocessing](sub-skills/encoders-preprocessing/SKILL.md) to choose `encoder_name`, list supported encoders, migrate deprecated `timm-` names, use `tu-` timm universal encoders, configure pretrained weights, or get preprocessing mean/std functions.
- Use [training-evaluation](sub-skills/training-evaluation/SKILL.md) for `DiceLoss`, `JaccardLoss`, `TverskyLoss`, `FocalLoss`, binary/multiclass/multilabel target shapes, `smp.metrics.get_stats`, IoU/F1/accuracy, or safe training/evaluation loops.
- Use [model-export](sub-skills/model-export/SKILL.md) for `save_pretrained`, `smp.from_pretrained`, changed class counts with `strict=False`, Hugging Face Hub sharing, ONNX, TorchScript, `torch.export`, or `torch.compile` readiness.
- Use [repo-development](sub-skills/repo-development/SKILL.md) only when the user is editing an SMP checkout: adding models/encoders/losses, updating docs tables, selecting focused tests, or maintaining package metadata.

## Quick Install And Import Check

SMP is published as `segmentation-models-pytorch` on PyPI and imports as `segmentation_models_pytorch`:

```bash
pip install -U segmentation-models-pytorch
python - <<'PY'
import segmentation_models_pytorch as smp
print(smp.__version__)
print(sorted(smp.MODEL_ARCHITECTURES_MAPPING))
PY
```

For local repo work, install the current checkout in editable mode with its runtime dependencies. Add test or docs extras only when the task actually needs tests or documentation builds.

## Common Public APIs

- Model constructors: `smp.Unet`, `smp.UnetPlusPlus`, `smp.MAnet`, `smp.Linknet`, `smp.FPN`, `smp.PSPNet`, `smp.PAN`, `smp.DeepLabV3`, `smp.DeepLabV3Plus`, `smp.UPerNet`, `smp.Segformer`, `smp.DPT`.
- Generic model factory: `smp.create_model(arch, encoder_name="resnet34", encoder_weights="imagenet", in_channels=3, classes=1, **kwargs)`.
- Encoder utilities: `smp.encoders.get_encoder_names()`, `get_encoder(...)`, `get_preprocessing_params(...)`, and `get_preprocessing_fn(...)`.
- Losses and modes: `smp.losses.BINARY_MODE`, `MULTICLASS_MODE`, `MULTILABEL_MODE`, plus Dice, Jaccard, Tversky, Focal, Lovasz, SoftBCE, SoftCE, and MCC losses.
- Metrics: `smp.metrics.get_stats(...)` followed by `iou_score`, `f1_score`, `accuracy`, `precision`, `recall`, or related rates.
- Persistence: `model.save_pretrained(...)` and `smp.from_pretrained(...)` for local directories or Hub repos when network and credentials are available.

## Safe Defaults

- Prefer `encoder_weights=None` for offline smoke tests to avoid downloading pretrained weights.
- Use small tensor sizes such as `64x64` or `128x128` for shape checks; do not run notebook-scale training or dataset downloads unless the user explicitly requests them.
- Use `classes=1` for binary logits, `classes=N` for multiclass/multilabel logits, and choose the matching loss/metric mode in [training-evaluation](sub-skills/training-evaluation/SKILL.md).
- Treat Hugging Face Hub pushes, pretrained checkpoint downloads, ONNX export, and long training examples as optional/networked workflows with explicit prerequisites.

## When To Refresh This Skill

Refresh this skill when SMP changes model constructors, architecture registry names, encoder registry behavior, pretrained weight handling, loss/metric signatures, save/load APIs, export compatibility, package dependencies, or maintainer test conventions. Use [Repository Provenance](references/repo-provenance.md) to compare the current checkout against the generation baseline.
