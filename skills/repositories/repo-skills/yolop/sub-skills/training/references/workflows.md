# YOLOP Training Workflows

## When to read

Read this when configuring `tools/train.py`, choosing end-to-end versus staged training, handling checkpoints, or preparing a safe dry run before long BDD100K training.

## Source command shapes

```bash
# From a YOLOP checkout root after editing/patching cfg.DATASET roots
PYTHONPATH=. python tools/train.py

# Distributed training on N GPUs
PYTHONPATH=. python -m torch.distributed.launch --nproc_per_node=N tools/train.py
```

`tools/train.py` parser options include `--modelDir`, `--logDir`, `--dataDir`, `--prevModelDir`, `--sync-bn`, `--local_rank`, `--conf-thres`, and `--iou-thres`. In the current source, `update_config` meaningfully applies `--logDir` and partially records `--modelDir`; it does not apply `--dataDir`, `--prevModelDir`, or the threshold overrides.

## Data and transforms

Training instantiates:

```python
train_dataset = dataset.BddDataset(cfg, is_train=True, inputsize=cfg.MODEL.IMAGE_SIZE, transform=ToTensor+Normalize)
valid_dataset = dataset.BddDataset(cfg, is_train=False, inputsize=cfg.MODEL.IMAGE_SIZE, transform=ToTensor+Normalize)
```

Use the data-preparation sub-skill first because `BddDataset` iterates drivable masks and then derives image, detection JSON, and lane paths.

The training transform path includes resize, letterbox, random perspective, HSV augmentation, horizontal flip, target xyxy/xywh conversion, and two-channel drivable/lane masks.

## Model and optimizer setup

`tools/train.py`:

1. Creates logger and TensorBoardX writer under `cfg.LOG_DIR`.
2. Selects device with `select_device`; CUDA is used when available unless debug/CPU behavior is forced.
3. Builds `model = get_net(cfg).to(device)`.
4. Creates `criterion = get_loss(cfg, device=device)`.
5. Creates optimizer via `get_optimizer(cfg, model)` using `TRAIN.OPTIMIZER` (`adam` by default, `sgd` supported).
6. Configures cosine learning-rate scheduler with warmup.

## Checkpoint loading and saving

Loading behavior:

- `cfg.MODEL.PRETRAINED`: full checkpoint; loads `state_dict` and optimizer; sets `begin_epoch`.
- `cfg.MODEL.PRETRAINED_DET`: detection-branch partial initialization using parameter index ranges.
- `cfg.AUTO_RESUME`: looks for `checkpoint.pth` under `cfg.LOG_DIR/cfg.DATASET.DATASET`.

Saving behavior:

- Every epoch saves `epoch-{epoch}.pth` under the timestamped final output directory.
- Every epoch also saves `checkpoint.pth` under `cfg.LOG_DIR/cfg.DATASET.DATASET`.
- At the end, `final_state.pth` stores only the model state dict in the final output directory.

## Training modes

The source uses parameter index ranges:

```text
Encoder: 0-16
Detection head: 17-24
Drivable-area segmentation head: 25-33
Lane-line segmentation head: 34-42
```

Mode flags:

| Flag | Effect |
| --- | --- |
| `TRAIN.SEG_ONLY` | Freeze encoder + detection head; train both segmentation branches. |
| `TRAIN.DET_ONLY` | Freeze encoder + both segmentation heads; train detection branch. |
| `TRAIN.ENC_SEG_ONLY` | Freeze detection head; train encoder + segmentation branches. |
| `TRAIN.ENC_DET_ONLY` | Freeze both segmentation heads; train encoder + detection branch. |
| `TRAIN.LANE_ONLY` | Freeze encoder + detection + drivable branches; train lane branch. |
| `TRAIN.DRIVABLE_ONLY` | Freeze encoder + detection + lane branches; train drivable branch. |

`MultiHeadLoss` zeros loss components to match these modes, so avoid contradictory flags.

## Auto-anchor

If `cfg.NEED_AUTOANCHOR=True`, training calls `run_anchor(logger, train_dataset, model, thr=cfg.TRAIN.ANCHOR_THRESHOLD, imgsz=min(cfg.MODEL.IMAGE_SIZE))` before the loop. This reads labels from the full training dataset, runs k-means plus genetic evolution, and mutates the detector anchors in memory. Use only when the dataset is ready and you intend to train.

## Safe dry-run pattern

Use the bundled smoke before full training:

```bash
python sub-skills/training/scripts/train_smoke.py --repo-root /path/to/YOLOP --device cpu --image-size 128
```

Add `--check-loss` only if you want to test `MultiHeadLoss`; on newer torch versions, the source `build_targets` clamp behavior may need a small compatibility patch documented in troubleshooting.
