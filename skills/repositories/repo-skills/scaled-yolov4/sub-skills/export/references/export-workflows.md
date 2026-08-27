# Export workflows

## Main export entry point

The bundled concrete export entrypoint is `runtime/models/export.py`. Run it through `scripts/run_export.py` so the working directory and `PYTHONPATH` point at the packaged runtime mirror:

```bash
python sub-skills/export/scripts/run_export.py --dry-run -- --weights weights.pt --img-size 640 640 --batch-size 1
```

The export path centers on:

- `models/export.py`

The script loads a checkpoint, marks the detect head for export, performs a dry run, and then tries three export targets:

- TorchScript
- ONNX
- CoreML

## Important inputs

- `--weights` for the checkpoint.
- `--img-size` for the export input shape.
- `--batch-size` for the dry-run batch shape.

## Export pipeline details

### TorchScript

- `torch.jit.trace` is used for tracing.
- The traced model is saved with a `.torchscript.pt` suffix.

### ONNX

- The model is fused before export.
- `torch.onnx.export` writes the ONNX file.
- `onnx.load` and `onnx.checker.check_model` are used to verify the artifact.

### CoreML

- `coremltools` is only available when the optional dependency is installed.
- The conversion starts from the TorchScript trace and uses image scaling compatible with the detection preprocessing path.

## Format selection guidance

- Use TorchScript when you want a PyTorch-native deployable artifact.
- Use ONNX when your downstream runtime understands the ONNX graph.
- Use CoreML only when the platform and dependency stack actually support it.

## Export checklist

- The runtime bundle is complete: `python scripts/check_runtime_bundle.py`.
- The checkpoint exists.
- The model can be loaded in the current environment.
- The chosen backend package is installed.
- The requested input shape is sensible for the downstream runtime.
- The environment can run the dry-run forward pass that precedes conversion.

Use `scripts/check_export_env.py` for optional dependency checks, then use `scripts/run_export.py --dry-run -- ...` to preview the concrete bundled `runtime/models/export.py` command before removing `--dry-run`.
