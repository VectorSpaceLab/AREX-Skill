# Export and backend workflows

## Purpose

Use this file for the concrete export choices and runtime compatibility notes.

## TorchScript export

TorchScript export is centered on `export_torchscript.py` and the
`MattingRefine_TorchScriptWrapper` pattern from the repo source.
The wrapper hoists the mutable inference attributes so callers can change them
after loading the scripted module.

Safe smoke first:

```bash
python sub-skills/export-and-backends/scripts/check_export_support.py \
  --repo-root <repo-checkout> \
  --device cpu
```

If you only want the exact source command shape, use the dry-run wrapper:

```bash
python sub-skills/export-and-backends/scripts/run_export_torchscript.py \
  --repo-root <repo-checkout> \
  --dry-run \
  -- \
  --model-backbone mobilenetv2 \
  --model-checkpoint <checkpoint> \
  --precision float32 \
  --output <torchscript-path>
```

## ONNX export

ONNX export is centered on `export_onnx.py`. The important choices are:

- model type: `mattingbase` or `mattingrefine`
- patch crop method: `unfold`, `roi_align`, or `gather`
- patch replace method: `scatter_nd` or `scatter_element`
- validation: optional `--validate` pass with ONNX Runtime

Safe smoke first:

```bash
python sub-skills/export-and-backends/scripts/check_export_support.py \
  --repo-root <repo-checkout> \
  --device cpu
```

Install `onnx` as well as `onnxruntime` if you want the ONNX branch of the
smoke to run.

If you only want the exact source command shape, use the dry-run wrapper:

```bash
python sub-skills/export-and-backends/scripts/run_export_onnx.py \
  --repo-root <repo-checkout> \
  --dry-run \
  -- \
  --model-type mattingrefine \
  --model-backbone mobilenetv2 \
  --model-checkpoint <checkpoint> \
  --onnx-opset-version 12 \
  --output <onnx-path> \
  --validate
```

## Compatibility notes

- `roi_align` and `scatter_element` are the safest compatibility defaults when
  a target backend struggles with patch operations.
- `unfold` and `scatter_nd` are attractive performance defaults when the target
  backend supports them.
- `float16` is not a safe default on CPU.
- Export validation is stricter when the model shape and ops are simple; the
  dummy smoke keeps the model tiny to reduce export risk.

## When to choose which backend

- Choose TorchScript when you need a self-contained scripted model with the same
  PyTorch behavior.
- Choose ONNX when you need interop with ONNX Runtime or another runtime that
  consumes ONNX graphs.
- Stay on PyTorch when you only need research-time inspection or model
  debugging.
