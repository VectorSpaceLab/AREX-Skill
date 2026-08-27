# Model Converter Reference

MMYOLO package model-converter commands rewrite upstream YOLO-family checkpoint keys into MMYOLO-compatible checkpoints. They do not retrain, export ONNX, or validate accuracy.

## Rules of thumb

- Pick the converter by the **upstream family**, not by the final MMYOLO model family.
- Each converter expects a family-specific checkpoint layout such as `model`, `ema`, or a `state_dict`.
- Conversion is a key-remap step only; it is safe to run before fine-tuning when the source checkpoint is trusted.
- Use the matching command for the source family version. Do not mix YOLOv5/6/7/8 converters.
- Prefer package-level `mim run mmyolo model_converters:<name>` commands so the workflow does not depend on a source checkout script path.

## Family map

| Source family | MIM command name | CLI shape | Source checkpoint expectation | Notes |
| --- | --- | --- | --- | --- |
| YOLOv5 | `model_converters:yolov5_to_mmyolo` | `--src SRC --dst DST` | `torch.load(src)['model']` with a P5/P6 layout | The mapping is selected by source name; P6 is detected from filename. It removes anchor/grid keys and rewrites the detection head. |
| YOLOv5u | `model_converters:yolov5u_to_mmyolo` | `--src SRC --dst DST` | `torch.load(src)['model']` | Similar to YOLOv5 but with the YOLOv5u head layout. |
| YOLOv6 | `model_converters:yolov6_to_mmyolo` | `--src SRC --dst DST` | `ema` when present, otherwise `model` | Handles ER blocks, reduce layers, rep-style paths, and detection head projections. |
| YOLOv6 v3 | `model_converters:yolov6_v3_to_mmyolo` | `--src SRC --dst DST` | `ema` when present, otherwise `model` | Extends the YOLOv6 mapping with v3-specific head and bifusion paths. |
| YOLOv7 | `model_converters:yolov7_to_mmyolo` | `SRC DST` | `torch.load(src)['model']` | The basename selects the mapping for `yolov7.pt`, `yolov7x.pt`, `yolov7-tiny.pt`, `yolov7-w6.pt`, `yolov7-e6.pt`, or `yolov7-e6e.pt`. P6 families may omit auxiliary-module weights. |
| YOLOv8 | `model_converters:yolov8_to_mmyolo` | `--src SRC --dst DST` | `torch.load(src)['model']` | Rewrites the head, proto path, and DFL-related weights. |
| YOLOX | `model_converters:yolox_to_mmyolo` | `--src SRC --dst DST` | `torch.load(src)['model']` | Remaps stem, backbone, neck, and head keys in component-specific helpers. |
| PPYOLOE | `model_converters:ppyoloe_to_mmyolo` | `--src SRC --dst DST [--imagenet-pretrain]` | Paddle checkpoint or ImageNet pretrain source | `--imagenet-pretrain` keeps the backbone-only path. The converter handles BN/RepVGG and head-specific names. |
| RTMDet | `model_converters:rtmdet_to_mmyolo` | `SRC DST` | `torch.load(src)['state_dict']` | Remaps neck blocks, bbox head, and data preprocessor keys. |

## Conversion recipes

### YOLOv5 and YOLOv5u

```bash
mim run mmyolo model_converters:yolov5_to_mmyolo --src SOURCE.pt --dst OUTPUT.pth
mim run mmyolo model_converters:yolov5u_to_mmyolo --src SOURCE.pt --dst OUTPUT.pth
```

Use these when the upstream checkpoint is a PyTorch `.pt` file with a `model` object inside.

### YOLOv6 and YOLOv6 v3

```bash
mim run mmyolo model_converters:yolov6_to_mmyolo --src SOURCE.pt --dst OUTPUT.pth
mim run mmyolo model_converters:yolov6_v3_to_mmyolo --src SOURCE.pt --dst OUTPUT.pth
```

These commands load `ema` when available and otherwise fall back to `model`.

### YOLOv7

```bash
mim run mmyolo model_converters:yolov7_to_mmyolo SOURCE.pt OUTPUT.pth
```

The basename of `SOURCE.pt` must match one of the supported YOLOv7 family names so the converter can choose the right mapping dictionary.

### YOLOv8

```bash
mim run mmyolo model_converters:yolov8_to_mmyolo --src SOURCE.pt --dst OUTPUT.pth
```

This converter is for the Ultralytics-style checkpoint that exposes `torch.load(src)['model']`.

### YOLOX

```bash
mim run mmyolo model_converters:yolox_to_mmyolo --src SOURCE.pth --dst OUTPUT.pth
```

The command groups keys by stem, backbone, neck, and head before renaming them.

### PPYOLOE

```bash
mim run mmyolo model_converters:ppyoloe_to_mmyolo --src SOURCE.pdparams --dst OUTPUT.pth
mim run mmyolo model_converters:ppyoloe_to_mmyolo --src SOURCE.pdparams --dst OUTPUT.pth --imagenet-pretrain
```

Use the ImageNet flag only when the source checkpoint contains backbone-only weights.

### RTMDet

```bash
mim run mmyolo model_converters:rtmdet_to_mmyolo SOURCE.pth OUTPUT.pth
```

This path loads the state dict, renames the supported keys, and saves the new checkpoint.

## What to watch for

- Wrong family selection usually shows up as missing keys or unmapped head blocks.
- Source checkpoints with a different internal layout than the converter expects must be treated as unsupported until the mapping is updated.
- If a converter uses a basename decision, make sure the source file name matches the intended family variant.
- If `mim run mmyolo --help` does not list converter commands, repair the MMYOLO package/MIM installation before relying on conversion commands.
