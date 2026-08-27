# Demo and Visualization Workflows

YOLOv7-d2's PyTorch demo pattern builds a Detectron2 model from a config, loads `MODEL.WEIGHTS`, resizes each input with `ResizeShortestEdge`, runs `model([inputs])`, and visualizes boxes/masks with Alfred/OpenCV utilities.

## Image or directory demo

```bash
python demo.py \
  --config-file path/to/config.yaml \
  --input path/to/image_or_directory \
  --output path/to/output_dir \
  -c 0.30 \
  -n 0.60 \
  --opts MODEL.WEIGHTS path/to/model.pth
```

Use `--output` in headless environments. Without it, the source demo uses OpenCV windows.

## CPU smoke demo

For a small correctness smoke, force CPU and use a single image:

```bash
python demo.py \
  --config-file path/to/config.yaml \
  --input path/to/image.jpg \
  --output path/to/out.jpg \
  --opts MODEL.WEIGHTS path/to/model.pth MODEL.DEVICE cpu
```

The source `demo.py` also sets `cfg.MODEL.DEVICE` from `torch.cuda.is_available()`, so an override may be overwritten in some versions. If CPU is mandatory, inspect or patch the user's demo launcher so the override is applied after device auto-selection.

## W&B inference logging

The demo accepts:

```bash
--wandb-project PROJECT --wandb-entity ENTITY
```

Only use this when the user has W&B configured and wants remote logging. It is not required for local visualization.

## Video and webcam

The docs show video-style demos for SparseInst, but video/webcam behavior depends on OpenCV codecs/display availability. Prefer saving output files and test with one frame/image before long video runs.

## Advanced data-cleaning script

The source includes a data-cleaning script built around predictions. Treat it as reference-only: it can influence dataset curation, requires model weights, and should not be run without explicit user intent and backups.
