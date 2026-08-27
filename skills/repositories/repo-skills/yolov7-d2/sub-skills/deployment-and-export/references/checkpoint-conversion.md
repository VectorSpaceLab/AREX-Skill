# DETR Checkpoint Conversion

YOLOv7-d2 includes converters for reference DETR, AnchorDETR, and SMCA-style checkpoints so their keys match Detectron2-style model names. The bundled helper unifies behavior distilled from `tools/convert_detr_to_d2.py`, `tools/convert_anchordetr_to_d2.py`, and `tools/convert_smcadetr_to_d2.py`.

## Use the bundled converter

```bash
python scripts/convert_detr_checkpoint.py \
  --source-model path/to/reference_checkpoint.pth \
  --output-model path/to/converted.pth \
  --variant detr
```

For AnchorDETR-style 91-class mapping:

```bash
python scripts/convert_detr_checkpoint.py --source-model path/to/src.pth --output-model path/to/out.pth --variant anchordetr
```

For segmentation/mask models, add `--mask` when the user's target model needs the extra backbone key prefixing behavior.

## What conversion does

- Loads `checkpoint["model"]` from a local file or URL.
- Rewrites ResNet backbone keys from reference naming to Detectron2 backbone naming.
- Prefixes every key with `--prefix` (default `detr`, matching YOLOv7-d2 wrappers that store DETR-family modules under `self.detr`; override only for custom code).
- Remaps COCO classifier rows from 91/92 reference class layouts to YOLOv7-d2/Detectron2 contiguous layout where applicable.
- Saves `{"model": converted_state_dict}`.

## Safety notes

- Conversion does not verify architecture compatibility. The target config must still match hidden sizes, query counts, mask mode, and backbone.
- URL input is blocked unless `--allow-url` is supplied; prefer local files unless the user explicitly requests URL conversion.
- Inspect a few printed key mappings before trusting the output.
