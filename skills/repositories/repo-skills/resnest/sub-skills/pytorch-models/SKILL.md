---
name: pytorch-models
description: "Use ResNeSt's PyTorch package and Torch Hub models,
  Split-Attention layers, safe no-pretrained inference, ImageNet config
  interpretation, and PyTorch troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyTorch Models

Use this sub-skill when the task is about the PyTorch side of ResNeSt: package imports, Torch Hub loading, model factories, Split-Attention layers, safe smoke checks, or PyTorch training/config interpretation.

## Read first

- Read [references/api-reference.md](references/api-reference.md) when you need model names, signatures, registry behavior, or Torch Hub entry points.
- Read [references/workflows.md](references/workflows.md) when you need a safe no-pretrained smoke, a Torch Hub loading recipe, or a distilled ImageNet verification flow.
- Read [references/training-and-configs.md](references/training-and-configs.md) when you need the bundled training config keys, dataset layout, loss selection, or launcher semantics.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports, pretrained weights, tensor shapes, cache behavior, or dataset layout fail.
- Run [scripts/pytorch_tiny_inference.py](scripts/pytorch_tiny_inference.py) for a safe offline-first model smoke and optional Split-Attention check.

## Covers

- Public PyTorch factories: `resnest50`, `resnest101`, `resnest200`, `resnest269`, and the fast variants `resnest50_fast_1s1x64d`, `resnest50_fast_2s1x64d`, `resnest50_fast_4s1x64d`, `resnest50_fast_1s2x40d`, `resnest50_fast_2s2x40d`, `resnest50_fast_4s2x40d`, `resnest50_fast_1s4x24d`.
- Registry-backed builders and internals: `get_model`, `ResNet`, `Bottleneck`, `SplAtConv2d`, and `rSoftMax`.
- Safe `pretrained=False` inference by default, with explicit warnings for any weight download attempt.
- ImageNet transform, loss, scheduler, and config interpretation at the level needed for future agents.
- PyTorch-specific troubleshooting for optional dependencies, pretrained cache, classifier-head mismatch, and unsupported layer settings.

## Does not cover

- Gluon / MXNet model zoo workflows.
- Detectron2 backbone and COCO workflows.
- Full ImageNet extraction or training launchers.

When a task leaves the classification path and moves into Gluon or Detectron2, route it to the sibling sub-skill for that backend instead of extending this one.
