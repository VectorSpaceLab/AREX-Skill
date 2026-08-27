# Config and Model Selection

YOLOv7-d2 is configured through Detectron2 Yacs configs and a smaller set of Python LazyConfigs. Always call `add_yolo_config(cfg)` before merging a YOLOv7-d2 YAML config.

## Meta-architecture routes

| Meta-architecture | Typical task | Trainer route | Notes |
|---|---|---|---|
| `YOLO`, `YOLOV5`, `YOLOV6`, `YOLOV7`, `YOLOV7P`, `YOLOX` | one-stage detection | standard detection | Usually uses YOLO config keys and custom YOLO dataset mapper. |
| `YOLOF` | anchor-free/YOLOF style detection | standard detection | Has a separate base config family. |
| `YOLOMask` | detection plus mask/orientation experiments | standard or instance workflow depending on config | Treat as experimental unless user's config is verified. |
| `SparseInst` | instance segmentation without boxes-first assumptions | instance segmentation | Use mask-aware evaluation notes. |
| `SOLOv2` | instance segmentation | instance segmentation | Less central in docs; verify config availability. |
| `Detr`, `AnchorDetr`, `SMCADetr`, `DetrD2go` | transformer detectors | DETR/transformer | Uses `DetrDatasetMapper`, ADAMW, query/layer settings, and often RGB format. |

## Representative config checks

A merged config should expose:

- `MODEL.META_ARCHITECTURE`
- `MODEL.WEIGHTS` or an explicit user checkpoint override
- `DATASETS.TRAIN` and `DATASETS.TEST`
- `DATASETS.CLASS_NAMES` when custom class labels are needed
- `MODEL.YOLO.CLASSES` or family-specific class count
- `INPUT.FORMAT`, train/test sizes, augmentation flags
- `SOLVER.IMS_PER_BATCH`, `SOLVER.BASE_LR`, `SOLVER.MAX_ITER`, optimizer and AMP settings
- `OUTPUT_DIR`

Run:

```bash
python scripts/inspect_yolov7_config.py --config path/to/config.yaml --json
```

## Config override syntax

For Yacs/YAML configs, Detectron2 accepts trailing key/value pairs:

```bash
python train.py --config-file path/to/config.yaml MODEL.WEIGHTS path/to/model.pth MODEL.DEVICE cpu SOLVER.IMS_PER_BATCH 2
```

For LazyConfig, use dotted assignment syntax:

```bash
python train_lazy.py --config-file path/to/config.py train.init_checkpoint=path/to/model.pth train.device=cuda
```

## Common config pitfalls

- `_BASE_` path casing matters. Some source configs reference `Base-YoloV7.yaml` while the observed base is `Base-YOLOv7.yaml`; fix the path before debugging model code.
- `DATASETS.TRAIN`/`TEST` names must match Detectron2 registered names.
- `MODEL.YOLO.CLASSES` should match the number of categories in the dataset for YOLO-family configs.
- Transformer backbones usually need pretrained weights or a deliberate scratch-training decision.
- W&B config flags do not prevent importing `wandb`; install it or patch the logger import in a user's environment.
