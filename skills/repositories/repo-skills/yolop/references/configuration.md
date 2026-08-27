# YOLOP Configuration Reference

## When to read

Read this before changing dataset paths, training modes, image size, GPU settings, optimizer options, checkpoints, or evaluation thresholds. YOLOP centralizes most runtime behavior in `lib/config/default.py` as a yacs `CfgNode` named `cfg`.

## Source-root import pattern

Most source scripts do this before importing `lib`:

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from lib.config import cfg, update_config
```

Bundled helper scripts avoid relying on their location by accepting `--repo-root` and adding that path to `sys.path` explicitly.

## Important config fields

| Field | Default role | Notes |
| --- | --- | --- |
| `LOG_DIR` | `runs/` | Training/evaluation logs and checkpoints are nested under dataset/model/time folders. |
| `GPUS` | `(0, 1)` | Used to compute batch sizes and DataParallel/validation batch behavior. If running CPU-only, be careful that batch size calculations still multiply by `len(cfg.GPUS)`. |
| `WORKERS` | `8` | Dataloader workers. Lower this for constrained CI, notebooks, or tiny smoke tests. |
| `PIN_MEMORY` | `False` | Can be enabled for CUDA dataloaders, but not needed for CPU smoke. |
| `AUTO_RESUME` | `False` | When true, `tools/train.py` looks for `checkpoint.pth` under `cfg.LOG_DIR/cfg.DATASET.DATASET`. |
| `NEED_AUTOANCHOR` | `False` | When true, training recomputes anchors from the training dataset using k-means/evolution. Requires labels and is not a cheap smoke check. |
| `MODEL.IMAGE_SIZE` | `[640, 640]` | Used for train/eval model inputs; demo CLI also has `--img-size`. Keep multiples of max stride 32. |
| `MODEL.PRETRAINED` | `""` | Full checkpoint to resume/load before training. |
| `MODEL.PRETRAINED_DET` | `""` | Detection-branch checkpoint for partial initialization. |
| `DATASET.DATAROOT` | source author's absolute BDD image path | Must be changed for a new checkout or run. |
| `DATASET.LABELROOT` | source author's absolute detection-label path | Must point to BDD-style JSON annotations. |
| `DATASET.MASKROOT` | source author's drivable-mask path | Must point to generated drivable-area PNG masks. |
| `DATASET.LANEROOT` | source author's lane-mask path | Must point to lane-line PNG masks. |
| `DATASET.DATASET` | `BddDataset` | Resolved by `eval('dataset.' + cfg.DATASET.DATASET)`. |
| `TRAIN.END_EPOCH` | `240` | Full training is long-running. Reduce only for experiments/smokes with clear expectations. |
| `TRAIN.BATCH_SIZE_PER_GPU` | `24` | Effective batch often multiplies by `len(cfg.GPUS)`. |
| `TEST.BATCH_SIZE_PER_GPU` | `24` | Used by evaluation; can be too large for CPU. |
| `TEST.NMS_CONF_THRESHOLD` | `0.001` | Native `tools/test.py` parses `--conf_thres` but `update_config` currently does not apply it. |
| `TEST.NMS_IOU_THRESHOLD` | `0.6` | Same caveat as confidence threshold. |

## CLI override caveats

`update_config(cfg, args)` only applies a small subset of parsed CLI fields in the current source:

- `--modelDir` sets `cfg.OUTPUT_DIR` if provided, but `OUTPUT_DIR` is otherwise not central in the visible source.
- `--logDir` sets `cfg.LOG_DIR`.
- Detection/evaluation threshold overrides are parsed but the assignments are commented out.
- `--dataDir` and `--prevModelDir` are parsed by `tools/train.py` but not applied by `update_config`.

If a task needs reliable dataset-root or threshold changes, edit a copied config module, patch `cfg` before calling the workflow, or modify `update_config` in the live checkout. Do not assume the parser option changed the yacs config unless the source assignment exists.

## Training-mode switches

The default end-to-end multitask behavior uses all of these as `False`:

```python
TRAIN.SEG_ONLY = False
TRAIN.DET_ONLY = False
TRAIN.ENC_SEG_ONLY = False
TRAIN.ENC_DET_ONLY = False
TRAIN.DRIVABLE_ONLY = False
TRAIN.LANE_ONLY = False
```

The training script freezes parameter index ranges when these flags are true:

- `SEG_ONLY`: freeze encoder and detection head; train both segmentation branches.
- `DET_ONLY`: freeze encoder and segmentation heads; train detection branch.
- `ENC_SEG_ONLY`: freeze detection head; train encoder and segmentation branches.
- `ENC_DET_ONLY`: freeze segmentation heads; train encoder and detection branch.
- `LANE_ONLY`: freeze encoder, detection head, and drivable-area branch; train lane branch.
- `DRIVABLE_ONLY`: freeze encoder, detection head, and lane branch; train drivable-area branch.

`MultiHeadLoss` also zeros loss components according to these flags. Keep training-mode flags and expected loss terms aligned.

## Device behavior

`select_device(logger, device='', batch_size=None)` uses CUDA when available unless `device='cpu'` is requested. If a non-CPU device string is passed, it sets `CUDA_VISIBLE_DEVICES` and asserts `torch.cuda.is_available()`.

For CPU smoke tests, pass `device='cpu'` where a script supports it. For DDP or practical training, install a CUDA-capable torch/torchvision pair and make sure `TRAIN.BATCH_SIZE_PER_GPU * len(cfg.GPUS)` is divisible by the number of selected GPUs when batch-size checks apply.
