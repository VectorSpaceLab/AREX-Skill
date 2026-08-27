# Training and CLI troubleshooting

Start with safe preflights:

```bash
python scripts/inspect_training_config.py --config references/configs/rfdetr_small.yaml
python scripts/validate_dataset_layout.py data/my_dataset --task auto
```

They inspect config/data only; they do not train, instantiate a model, or download weights.

## Missing extras and imports

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` importing `pytorch_lightning`, `torchmetrics`, `pycocotools`, or training modules | Training extra absent | `pip install "rfdetr[train]"` |
| `rfdetr` CLI cannot parse signatures/configs or `jsonargparse` is missing | CLI extra absent | `pip install "rfdetr[train,cli]"` |
| Custom `aug_config` or `augmentation_backend="albumentations"` fails | Augment extra absent | `pip install "rfdetr[train,augment]"` |
| `augmentation_backend="kornia"` fails despite augment extra | No CUDA device, no Kornia, or keypoint task | Use `cpu`/`auto`, install augment, or avoid Kornia for keypoints |
| TensorBoard/W&B/MLflow missing | Logger extra or credential/config missing | `pip install "rfdetr[train,loggers]"`; run `wandb login` or set MLflow env vars |
| `clearml=True` raises | Native ClearML logger is not implemented | Initialize ClearML SDK before training; omit `clearml=True` |

## Dataset detection failures

Auto-detection under `dataset_file="roboflow"` requires either:

- COCO: `train/_annotations.coco.json`; or
- YOLO: `data.yaml`/`data.yml` plus `train/images/`.

For YOLO training, also ensure `train/labels/` and `valid/` or `val/` with matching `images/` and `labels/`. For Roboflow COCO, use `valid/` rather than native `val2017/`. Explicitly set `dataset_file="coco"` for native COCO and `dataset_file="yolo"` to force YOLO.

## COCO layout and class/schema mismatch

Check that COCO JSON roots are objects with `images`, `annotations`, and `categories` lists. Every annotation `category_id` must exist in categories and every `image_id` must exist in images. Boxes are COCO pixel `[x, y, width, height]`, not normalized YOLO center boxes.

Segmentation models require `segmentation` on object annotations. Detection-only COCO can train detection models but will not yield mask metrics.

Custom/Roboflow COCO categories are remapped to contiguous labels, and unannotated grouping categories can be filtered. If a fine-tuned checkpoint's class names or model `num_classes` do not match the dataset, evaluate warns and proceeds without adapting the head; train only auto-aligns when the user did not explicitly pin `num_classes`.

## YOLO layout and class/schema mismatch

YOLO failures usually mean:

- `names` is missing, empty, or a non-contiguous mapping.
- `nc` disagrees with the `names` count.
- Label class IDs are non-integer or outside `0..N-1`.
- Detection rows do not have five fields.
- Segmentation rows have an odd number of polygon coordinate values.
- YAML split paths escape the dataset root or resolve to directories without both `images` and `labels`.
- A declared test path is broken; RF-DETR treats that as invalid data, not as fallback-to-validation.

Missing label files and empty label files are allowed for true background images.

## Keypoint failures

- YOLO pose requires `kpt_shape: [K,2]` or `[K,3]`; a five-field detection row is not a pose row.
- Every YOLO pose row must have exactly `5 + K * dim` fields.
- For dim 3, visibility must be finite and in `[0,2]`; for dim 2, negative coordinates indicate absence and visibility is synthesized.
- COCO keypoint mode needs category `keypoints` metadata or annotation keypoint triples. A detection-only COCO file fails schema inference.
- Use `infer_coco_keypoint_schema(...)` or `infer_yolo_keypoint_schema(...)` to inspect `class_names`, `num_keypoints_per_class`, OKS sigmas, and flip pairs before training.
- Missing or ambiguous flip pairs intentionally disable horizontal flips in keypoint mode.
- Keypoints use DDP, not FSDP/DeepSpeed; use CPU/Albumentations rather than Kornia GPU augmentation.

## Config and resolution errors

`TrainConfig` forbids unknown fields. Put architecture-only fields under the model constructor/model config: `gradient_checkpointing`, `resolution`, `num_classes`, `num_keypoints_per_class`, `pretrain_weights`, `patch_size`, and `num_windows`. Put training/runtime fields under `TrainConfig`.

Resolution must be divisible by `patch_size * num_windows`. Common currently documented divisors: released detection variants usually use 32, most segmentation variants use 24, and segmentation nano uses a smaller block. The definitive rule is the selected model config's `patch_size * num_windows`.

If a Lightning YAML fails, verify class paths are under `rfdetr.config`, detection uses `TrainConfig`, segmentation uses `SegmentationTrainConfig`, and keypoint uses `KeypointTrainConfig`.

## Batch size, OOM, and slow training

- `batch_size="auto"` works only in the high-level Python API with CUDA. The CLI/custom datamodule needs a concrete integer.
- Effective batch is `batch_size * grad_accum_steps * num_gpus`; keep this stable when scaling GPU count.
- For OOM: lower `batch_size`, increase `grad_accum_steps`, lower a valid resolution, enable constructor-level `gradient_checkpointing=True`, disable EMA (`use_ema=False`) if acceptable, or choose a smaller model.
- For CPU input bottlenecks: increase `num_workers`, tune `pin_memory`, `persistent_workers`, and `prefetch_factor`, reduce expensive Albumentations transforms, or try `augmentation_backend="auto"`/Kornia on CUDA for non-keypoint tasks.
- Small datasets are sampled with replacement to fill enough effective batches; this is intentional.

## Augmentation backend issues

- `augmentation_backend="torchvision"` pins the default native pipeline.
- `augmentation_backend="cpu"` chooses the best installed CPU backend at dataset-build time.
- `augmentation_backend="auto"` prefers Kornia on CUDA, then CPU backends; saved configs stay portable.
- `augmentation_backend="albumentations"` requires Albumentations and is CPU-side.
- `augmentation_backend="kornia"` requires CUDA + Kornia and is unsupported for keypoint transforms.

Passing `aug_config={}` disables optional training augmentation such as horizontal flip. `scale_jitter=False` disables the separate resize/crop branch. Aggressive geometric transforms can move boxes or masks out of frame; reduce them when boxes disappear or validation greatly exceeds training mAP.

## Resume behavior

`last.ckpt` and `checkpoint_<epoch>.ckpt` are full Lightning checkpoints and restore model, optimizer, scheduler, epoch, and loop state. Best `.pth` files (`checkpoint_best_regular.pth`, `checkpoint_best_ema.pth`, `checkpoint_best_total.pth`, `last_ema.pth`) intentionally omit optimizer/scheduler state; they start those components cold.

Lightweight `.pth` files can include callback state in newer runs, but restoration requires matching callback configuration. Best-score history also requires the same `output_dir` because Lightning checkpoint callbacks gate state restoration by directory. If the goal is a new fine-tune from best weights, use `pretrain_weights=".../checkpoint_best_total.pth"` instead of `resume=`.

A fresh run reusing an output directory can reset CSV history. A truthy resume preserves `metrics.csv` history.

## DDP and devices

`devices` defaults to one. A `torchrun` launch can underuse GPUs unless the script/config sets `devices="auto"` or an explicit count plus a distributed strategy such as `ddp`.

```bash
torchrun --nproc_per_node=4 -m rfdetr fit \
  --config references/configs/rfdetr_small.yaml \
  --trainer.devices 4 \
  --trainer.strategy ddp
```

RF-DETR wraps DDP with `find_unused_parameters=True`. EMA is disabled for sharded strategies. Keypoint manual optimization synchronizes every microbatch, so keep keypoint `grad_accum_steps=1` on multi-GPU for throughput. Keypoint FSDP/DeepSpeed is unsupported.

## Logger, metric, and credential issues

CSVLogger is always present during training. TensorBoard missing/incompatible packages are downgraded to warnings. W&B needs login/API credentials. MLflow needs tracking URI/token configuration when using a remote server. `clearml=True` is not implemented as a native RF-DETR logger.

With `eval_ema_only=True`, use `val/ema_*` metrics; `val/mAP_*` or `val/segm_mAP_*` can be absent. Metric monitors differ by task: detection box mAP, segmentation mask mAP, and keypoint AP. `run_test=True` evaluates the best checkpoint at the end of training only when a best checkpoint exists.
