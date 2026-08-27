---
name: internals-maintenance
description: "Guides FCOS source internals, model/loss/postprocess components,
  compiled layers, focused tests, and legacy PyTorch compatibility maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# FCOS Internals and Maintenance

Use this sub-skill when the user is editing or debugging FCOS internals, including `FCOSHead`, `FCOSModule`, loss/postprocessing, `BoxList`, compiled C++/CUDA layers, test selection, or porting the legacy package to a newer PyTorch stack.

## Start here

1. Read [`references/architecture.md`](references/architecture.md) for how FCOS fits into the maskrcnn-benchmark detector stack.
2. Read [`references/api-reference.md`](references/api-reference.md) for component signatures and config keys consumed by internals.
3. Read [`references/testing-reference.md`](references/testing-reference.md) before selecting native tests.
4. Run [`scripts/inspect_fcos_components.py`](scripts/inspect_fcos_components.py) for safe import/config/component diagnostics.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) for `_C`, compiler, CUDA, NumPy, and PyTorch API drift.

## Boundaries

- Route ordinary image detection to [`../inference-demo/SKILL.md`](../inference-demo/SKILL.md).
- Route config/data layout questions to [`../data-configs/SKILL.md`](../data-configs/SKILL.md).
- Route train/eval command construction to [`../training-evaluation/SKILL.md`](../training-evaluation/SKILL.md).
- Route ONNX export consumer questions to [`../onnx-export/SKILL.md`](../onnx-export/SKILL.md).

## Maintenance principle

Use tests and source inspection to isolate a component before running expensive COCO jobs. Many unit tests are CPU-safe, but model/layer tests may depend on the compiled extension and legacy PyTorch compatibility.
