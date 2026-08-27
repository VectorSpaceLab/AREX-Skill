# Visualization and dataset previews

## Prediction visualization

AdelaiDet's demo flow builds a Detectron2-style config with AdelaiDet defaults, constructs a predictor, and writes/opens visualized outputs depending on input mode.

Key knobs:

- `--confidence-threshold`: filters predictions before drawing.
- `--output`: required on headless machines if you need saved images/video.
- `MODEL.WEIGHTS`: supplied by the wrapper through `--weights`.
- `MODEL.DEVICE`: override through `--opts` when forcing CPU/GPU.

Text models use AdelaiDet visualizer utilities to draw Bezier/text predictions. If the issue is OCR label quality, lexicons, or evaluation score interpretation, route to `text-spotting`.

## Dataset visualization

Use dataset visualization before training when you suspect annotation/category/mask/keypoint issues:

```bash
python scripts/visualize_dataset.py --repo-root /path/to/AdelaiDet \
  --config configs/BlendMask/R_50_1x.yaml --source dataloader --output output/dataset-vis --dry-run
```

Common source choices are controlled by the repository script; use `--help` to inspect the current parser. Typical sources include dataset dictionaries or dataloader samples.

## Headless environments

- Avoid webcam mode and GUI display windows.
- Always provide `--output` for image/video workflows.
- Prefer `opencv-python-headless` for servers.
- If video writing fails, check codec availability before assuming model failure.

## When visualization reveals data issues

Switch to `data-prep` if visual output shows:

- Category IDs shifted or missing.
- Empty masks or all-background semantic masks.
- Text annotations without Bezier control points.
- Keypoints in the wrong coordinate frame.
- Image paths that do not resolve from dataset registration metadata.
