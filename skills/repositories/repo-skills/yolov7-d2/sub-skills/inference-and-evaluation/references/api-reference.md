# Inference API and Flag Reference

## Source demo flags

The distilled `demo.py --help` exposed these user-facing flags:

- `--config-file FILE`
- `--webcam`
- `-i, --input INPUT`
- `-o, --output OUTPUT`
- `-c, --confidence-threshold FLOAT` (default observed: 0.21)
- `-n, --nms-threshold FLOAT` (default observed: 0.6)
- `--wandb-project NAME`
- `--wandb-entity NAME`
- `--opts KEY VALUE ...`

## Predictor behavior

The source `DefaultPredictor` pattern:

1. Clones the config.
2. Builds a Detectron2 model with `build_model(cfg)`.
3. Loads `cfg.MODEL.WEIGHTS` through `DetectionCheckpointer`.
4. Builds `ResizeShortestEdge([cfg.INPUT.MIN_SIZE_TEST, cfg.INPUT.MIN_SIZE_TEST], cfg.INPUT.MAX_SIZE_TEST)`.
5. Converts RGB/BGR as required by `cfg.INPUT.FORMAT`.
6. Runs `model([{"image": tensor, "height": h, "width": w}])` under `torch.no_grad()`.
7. Expects a Detectron2-style output dictionary whose `instances` may contain boxes, masks, scores, and classes.

## Visualization behavior

The source visualization uses Alfred helpers and OpenCV. For headless use, prefer writing outputs instead of opening a display window. If the user's environment lacks Alfred visualization modules, they can still run model prediction if they replace visualization with Detectron2 or custom output serialization.
