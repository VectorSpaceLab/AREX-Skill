---
name: automatic-mask-generation
description: "Generate masks for all objects in images or folders with Segment
  Anything's SamAutomaticMaskGenerator and the bundled AMG CLI. Use for batch
  automatic masks, PNG/CSV outputs, COCO RLE JSON, threshold tuning, crop
  settings, and memory-aware AMG runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Automatic Mask Generation

Use this sub-skill when the user wants SAM to segment all visible objects in an image or folder without point or box prompts. It covers `SamAutomaticMaskGenerator`, the bundled `scripts/amg_cli.py`, binary mask PNG folders, `metadata.csv`, COCO RLE JSON, threshold tuning, crop expansion, batching, and memory tradeoffs.

Do not use this sub-skill for prompted point/box/mask refinement; route those requests to `../prompted-segmentation/`. Do not use it for ONNX export, browser inference, or the web demo; route those requests to `../onnx-and-browser/`.

## Quick Start

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_b_01ec64.pth \
  --model-type vit_b \
  --input images/ \
  --output masks/ \
  --device cpu
```

For COCO-style RLE JSON instead of per-mask PNG folders:

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_h_4b8939.pth \
  --model-type vit_h \
  --input image.jpg \
  --output masks-rle/ \
  --convert-to-rle \
  --device cuda
```

## Routing

- Use `references/api-reference.md` for direct Python use of `SamAutomaticMaskGenerator` and returned annotation records.
- Use `references/cli-reference.md` for exact bundled CLI flags, output layout, and optional dependency checks.
- Use `references/workflows.md` for folder runs, COCO RLE conversion, threshold tuning, and avoiding GPU out-of-memory failures.
- Use `references/troubleshooting.md` for missing `cv2`, missing `pycocotools`, checkpoint/model mismatch, CPU fallback, unreadable images, empty output, and memory blowups.

## Key Defaults

- Registry keys are `default`, `vit_h`, `vit_l`, and `vit_b`; `default` is equivalent to the ViT-H builder.
- `SamAutomaticMaskGenerator(model)` defaults to `points_per_side=32`, `points_per_batch=64`, `pred_iou_thresh=0.88`, `stability_score_thresh=0.95`, `crop_n_layers=0`, `min_mask_region_area=0`, and `output_mode="binary_mask"`.
- `output_mode="coco_rle"` requires `pycocotools`; `min_mask_region_area > 0` requires OpenCV.
- Large images, high `points_per_side`, large `points_per_batch`, crop layers, and binary mask output all increase memory use.
