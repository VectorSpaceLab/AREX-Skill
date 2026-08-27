# Export workflows

## Source evidence

Torchreid's upstream exporter supports ONNX, OpenVINO, and TFLite-style export paths; use this sub-skill's bundled helper rather than relying on a source checkout.

The source exporter combines two important facts:

- `FeatureExtractor(model_name=..., model_path=...)` builds the architecture from `model_name` and then loads checkpoint weights from `model_path` when a file exists.
- The upstream exporter tries to infer the model name from the checkpoint filename, but its helper only recognizes a limited subset of names.

That means the bundled helper should accept an explicit `--model-name` and only fall back to filename inference when the checkpoint name is unambiguous.

## Export decision tree

1. Decide whether the checkpoint is already trained.
   - If not, route the request to `training-evaluation` first.
2. Resolve the core model family.
   - Prefer `--model-name`.
   - Fall back to filename inference only when a single known core model key is obvious.
3. Choose the export chain.
   - `onnx` alone: export a single ONNX artifact.
   - `openvino`: export ONNX first, then convert that ONNX file to OpenVINO.
   - `tflite`: export ONNX first, then OpenVINO, then the TFLite-style outputs.
4. Decide whether dynamic axes are needed.
   - Dynamic axes apply to the ONNX export stage.
   - Downstream converters may collapse or reinterpret the dynamic batch shape.
5. Decide whether FP16 is useful.
   - Keep the ONNX stage CPU-safe and float32 by default.
   - Use FP16 only when the OpenVINO converter is present and can accept it.

## Format matrix

| Requested value | Required chain | Typical artifact | Optional dependency gate | Notes |
| --- | --- | --- | --- | --- |
| `onnx` | checkpoint → model → ONNX | `*.onnx` | `onnx` and optional `onnxsim` | CPU-safe path; dynamic batch axis is supported here. |
| `openvino` | checkpoint → model → ONNX → OpenVINO | `*_openvino_model/` | ONNX first, then `openvino-dev` or the Model Optimizer entry point | OpenVINO is derived from the ONNX artifact, not from raw weights. |
| `tflite` | checkpoint → model → ONNX → OpenVINO → TFLite-style outputs | `*_tflite_model/` | OpenVINO first, then `openvino2tensorflow`, `tensorflow`, and related runtime packages | Treat this as a conversion chain, not a direct Torchreid export. |

## Typical export commands

### 1) Minimal ONNX export

```bash
python scripts/export_torchreid_model.py \
  --weights checkpoints/person_reid_best.pth.tar \
  --model-name osnet_x0_25 \
  --include onnx \
  --imgsz 256 128 \
  --opset 12
```

Use this when you want a deployment artifact but do not need downstream conversion frameworks.

### 2) ONNX plus OpenVINO

```bash
python scripts/export_torchreid_model.py \
  --weights checkpoints/person_reid_best.pth.tar \
  --model-name osnet_x0_25 \
  --include openvino \
  --dynamic
```

This still exports ONNX first, then attempts OpenVINO conversion from the ONNX file.

### 3) Full chain with dry-run planning

```bash
python scripts/export_torchreid_model.py \
  --weights checkpoints/person_reid_best.pth.tar \
  --model-name osnet_x0_25 \
  --include onnx openvino tflite \
  --dry-run
```

Use this to confirm the model family, artifact names, and dependency requirements before writing files.

## Validation checklist

- The checkpoint path exists and is readable.
- The resolved model name is a core Torchreid key.
- The checkpoint actually matches the chosen model family.
- ONNX export loads and passes `onnx.checker.check_model` when the package is installed.
- OpenVINO and TFLite requests are only attempted after ONNX exists.
- The helper prints a precise message when a requested optional dependency is missing.
- Do not claim the export is verified unless the artifact files were actually produced in the current environment.

## Practical notes

- The upstream exporter uses YOLO-derived status text and a pandas-backed format table; the bundled helper keeps messages Torchreid-specific and avoids requiring pandas for help or dry-run.
- `--dynamic` is most trustworthy at the ONNX stage.
- `--model-name` is the safest answer when the checkpoint filename does not encode the architecture.
- Existing outputs are protected unless `--force` is supplied.
- Project-specific architectures that are not part of the core build model registry are excluded long-tail gaps unless a future extension bundles the project sources.
