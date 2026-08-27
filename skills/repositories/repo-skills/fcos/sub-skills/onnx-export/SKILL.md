---
name: onnx-export
description: "Guides FCOS ONNX export command construction, output tensor
  contracts, backend constraints, and ONNX evaluation troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# FCOS ONNX Export

Use this sub-skill when the user asks to export an FCOS model to ONNX, inspect ONNX output tensors, test an ONNX FCOS file, handle Caffe2 backend constraints, or reduce ONNX export/evaluation memory.

## Start here

1. Read [`references/workflows.md`](references/workflows.md) for export and ONNX test flows.
2. Read [`references/output-contract.md`](references/output-contract.md) for dummy input and output tensor names/order.
3. Use [`scripts/build_onnx_export_command.py`](scripts/build_onnx_export_command.py) to produce a safe export command without running it.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) before installing ONNX/Caffe2 dependencies or running large exports.

## Boundaries

- Route config selection and dataset layout to [`../data-configs/SKILL.md`](../data-configs/SKILL.md).
- Route normal PyTorch train/eval to [`../training-evaluation/SKILL.md`](../training-evaluation/SKILL.md).
- Route one-image high-level detector demos to [`../inference-demo/SKILL.md`](../inference-demo/SKILL.md).
- Route source-level postprocessor edits to [`../internals-maintenance/SKILL.md`](../internals-maintenance/SKILL.md).

## Safety rule

ONNX export constructs the FCOS model and loads weights. ONNX testing may require datasets and the Caffe2 ONNX backend. Do not run export/test by default; build commands and validate prerequisites first.
