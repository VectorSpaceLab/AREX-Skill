# ONNX Export Reference

## When to Export

Export a MobileNet checkpoint when the C++ port needs an ONNX file such as `mb_1.onnx` or a converted training checkpoint such as `phase1_wpdc_vdc.onnx`.

The stock C++ predictor expects a 62-output MobileNet architecture:

```text
12 projection/pose/offset values + 40 shape coefficients + 10 expression coefficients = 62
```

Use `num_classes=62` unless you also update the C++ post-processing and basis data.

## Bundled Export Helper

Use the bundled script rather than the original ad-hoc conversion helper:

```bash
python sub-skills/cpp-onnx-port/scripts/export_mobilenet_to_onnx.py \
  --repo-root "$REPO" \
  --checkpoint weights/phase1_wpdc_vdc.pth.tar \
  --output c++/weights/phase1_wpdc_vdc.onnx \
  --arch mobilenet_1 \
  --num-classes 62
```

For the original C++ demo name, export or copy the model to:

```text
c++/weights/mb_1.onnx
```

or adapt the C++ model path consistently before rebuilding.

The helper resolves relative `--checkpoint` and `--output` paths against `--repo-root`. Its `--help` path is safe in environments without PyTorch; PyTorch is imported only after argument parsing when export work is actually requested.

## Original Conversion Logic Preserved

The original conversion flow did the following:

1. Load a checkpoint dictionary from `weights/mb_1.p` or `weights/phase1_wpdc_vdc.pth.tar`.
2. Read the `state_dict` entry.
3. Instantiate `mobilenet_v1.mobilenet_1(num_classes=62)`.
4. Remove a leading `module.` prefix from DataParallel-trained checkpoints.
5. Remap `fc_param.weight` to `fc.weight` and `fc_param.bias` to `fc.bias`.
6. Export with a dummy input shaped `1 x 3 x 120 x 120`.

The bundled helper keeps those model/key assumptions but adds explicit paths, shape checks, controlled missing-key behavior, and safer reporting.

## Checkpoint Key Rules

Expected key fixes:

```text
module.conv1.weight         -> conv1.weight
module.fc_param.weight      -> fc.weight
module.fc_param.bias        -> fc.bias
fc_param.weight             -> fc.weight
fc_param.bias               -> fc.bias
```

The helper fails by default when non-BatchNorm model keys are absent after remapping. Use `--allow-missing` only when intentionally exporting a partial or diagnostic model, because missing keys remain at initialization and can make landmarks meaningless.

Unknown checkpoint keys are reported and skipped. A checkpoint that is not a state dict, and does not contain the selected `--checkpoint-key`, is rejected.

## Architecture Choices

The MobileNet factories exposed by the repository model file are:

```text
mobilenet_2
mobilenet_1
mobilenet_075
mobilenet_05
mobilenet_025
```

The C++ demo default is `mobilenet_1`. If a checkpoint was trained with a different width multiplier, pass the matching factory with `--arch`; otherwise tensor shape mismatches will prevent a safe export.

## Export Validation

After export:

```bash
test -s "$REPO/c++/weights/phase1_wpdc_vdc.onnx"
```

If OpenCV Python bindings are available, a lightweight readability probe can catch obvious ONNX/OpenCV incompatibility before C++ debugging:

```bash
python - <<'PY'
import cv2
net = cv2.dnn.readNetFromONNX('c++/weights/phase1_wpdc_vdc.onnx')
print('ONNX loaded by OpenCV DNN')
PY
```

If the C++ demo still uses `weights/mb_1.onnx`, either place the exported model at that exact name or update the C++ predictor path before rebuilding.
