# Python training and evaluation workflows

Training dependencies are optional. Use public package installs in user-facing instructions:

```bash
pip install "rfdetr[train]"
pip install "rfdetr[train,augment,loggers]"
```

RF-DETR has a high-level path and a custom Lightning path. Both use the same `RFDETRModelModule`, `RFDETRDataModule`, callbacks, metric code, and `build_trainer` stack.

## High-level API

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall()
model.train(
    dataset_dir="data/detection",
    epochs=100,
    batch_size=4,
    grad_accum_steps=4,
    lr=1e-4,
    output_dir="outputs/detection",
)
```

Use `RFDETRSegSmall` for instance segmentation. Use `RFDETRKeypointPreview` for pose/keypoint data and either let training infer the schema or pass `num_keypoints_per_class`, `keypoint_oks_sigmas`, and `keypoint_flip_pairs` explicitly.

`RFDETR.train(self, **kwargs) -> None`:

1. Imports the optional training stack; missing dependencies should be fixed with `pip install "rfdetr[train,loggers]"` or the narrower extras required by the run.
2. Builds a `TrainConfig` variant through the model wrapper. Unknown train fields raise Pydantic errors instead of being ignored.
3. Handles wrapper-only arguments: `device` maps to Lightning accelerator/devices, and `resolution` mutates the model config after checking divisibility by `patch_size * num_windows`.
4. Resolves `batch_size="auto"` on the high-level Python path by probing CUDA memory with forward/backward synthetic batches. This is train-only and not available in CLI/datamodule construction.
5. Aligns class count and keypoint metadata from the dataset when those fields were not explicitly pinned.
6. Creates `RFDETRModelModule`, `RFDETRDataModule`, and `build_trainer(...)`, then calls `trainer.fit(...)`.
7. Syncs trained weights and class names back to the wrapper and writes `training_config.json` from the main process.

## Evaluation

```python
from rfdetr import RFDETRSmall

model = RFDETRSmall(pretrain_weights="outputs/detection/checkpoint_best_total.pth")
metrics = model.evaluate(dataset_dir="data/detection", split="test")
print(metrics["test/mAP_50_95"])
```

`RFDETR.evaluate(self, *, split="test", **kwargs) -> dict[str, float]` evaluates the weights already in memory. It does not reload a checkpoint and does not adapt the model head to dataset class count. If dataset class count differs from `model_config.num_classes`, evaluation warns and proceeds unchanged.

- `split="val"` always evaluates validation.
- `split="test"` uses labelled Roboflow/YOLO test data when available; native COCO and unavailable YOLO test splits fall back to validation while retaining `test/*` metric keys.
- Training-only fields are accepted for convenience but have no effect in the eval-only trainer.
- Evaluation writes no checkpoints or logger files.
- `batch_size="auto"` is skipped in evaluation and falls back to the default micro-batch because the training probe would waste compute and under-size evaluation.

## Important configuration groups

| Concern | Fields / behavior |
| --- | --- |
| Data | `dataset_dir`, `dataset_file`, `class_names`, `num_workers` |
| Batch/runtime | `batch_size`, `grad_accum_steps`, `auto_batch_target_effective`, `accelerator`, `devices`, `strategy`, `num_nodes` |
| Optimization | `lr`, `lr_encoder`, `weight_decay`, `optimizer`, `optimizer_kwargs`, `fused_optimizer` |
| Schedule | `lr_scheduler`, `lr_scheduler_kwargs`, `warmup_epochs`, `lr_scheduler_interval`, `lr_scheduler_monitor` |
| Checkpoints | `output_dir`, `resume`, `checkpoint_interval`, `skip_best_epochs`, `smooth_alpha` |
| Regularization | `use_ema`, `ema_decay`, `ema_tau`, `ema_update_interval`, `drop_path`, `early_stopping*` |
| Evaluation | `eval_max_dets`, `eval_interval`, `eval_ema_only`, `log_per_class_metrics`, `run_test`, `eval_masks_head_resolution` |
| Data transforms | `aug_config`, `augmentation_backend`, `scale_jitter`, `multi_scale`, `expanded_scales`, `save_dataset_grids` |
| Logging | CSV always active in training mode; optional `tensorboard`, `wandb`, `mlflow`, `project`, `run`; `clearml` is not wired as a native logger |
| DataLoader tuning | `pin_memory`, `persistent_workers`, `prefetch_factor` |

`SegmentationTrainConfig` adds `mask_point_sample_ratio`, `mask_ce_loss_coef`, and `mask_dice_loss_coef`. `KeypointTrainConfig` sets keypoint losses to active defaults, `skip_best_epochs=10`, and `smooth_alpha=0.5` for noisy keypoint AP. `gradient_checkpointing` is a model-constructor/model-config field, not a train field: use `RFDETRSmall(gradient_checkpointing=True)`.

## Optimizer and scheduler selection

- Bare optimizer names (`adamw`, `sgd`, `adam`) resolve only native `torch.optim` optimizers; RF-DETR supplies learning rate and weight decay.
- Dotted optimizer paths (for example `torch.optim.AdamW` or `pytorch_optimizer.Lion`) receive RF-DETR parameter groups plus only `optimizer_kwargs`.
- A callable or `functools.partial` owns its hyperparameters; `optimizer_kwargs` is ignored. Non-importable callables can train but cannot round-trip through `training_config.json`.
- Managed scheduler names are only `step` and `cosine`. Explicit dotted schedulers need all required constructor kwargs. Managed `lr_drop`/`min_factor` belong in `lr_scheduler_kwargs`.
- Explicit schedulers can use warmup and `lr_scheduler_interval="epoch"`. `ReduceLROnPlateau` steps per epoch and reads `lr_scheduler_monitor`.
- Wrapper optimizers such as SAM/Lookahead need custom `configure_optimizers` and manual-optimization care.

## Batch and memory planning

```text
effective_batch_size = batch_size * grad_accum_steps * num_gpus
```

Common target-16 examples: 1 GPU uses `4 x 4`, 2 GPUs `4 x 2`, 4 GPUs `4 x 1`, and 8 GPUs `2 x 1`. On memory pressure, reduce micro-batch, increase accumulation, choose a smaller model, lower a valid resolution, or enable constructor-level gradient checkpointing.

`batch_size="auto"` probes only on CUDA and targets a per-device effective batch, so global effective batch also multiplies by `devices * num_nodes`. If a user puts `batch_size="auto"` in a CLI YAML, replace it with a concrete integer.

## Augmentation backends

Omitting `aug_config` uses torchvision-native default training augmentation: resize/crop scale jitter plus horizontal flip. Passing `aug_config={}` disables the horizontal flip while keeping required resizing and normalization. A non-empty `aug_config` requires `rfdetr[augment]` and selects Albumentations or Kornia depending on `augmentation_backend`.

| Value | Meaning |
| --- | --- |
| `torchvision` | Pin the native pipeline regardless of optional packages. Legacy alias: `tv`. |
| `cpu` | Late-pick the best installed CPU backend: Albumentations, then Kornia CPU, then torchvision. |
| `auto` | Prefer Kornia on CUDA, otherwise CPU selection. Portable saved sentinel. |
| `albumentations` | Force CPU Albumentations; requires the `augment` extra. Legacy alias: `albu`. |
| `kornia` | Force GPU-side Kornia; requires CUDA and the `augment` extra. Legacy alias: `gpu`. |

Built-in preset dicts include `AUG_CONSERVATIVE`, `AUG_AGGRESSIVE`, `AUG_AERIAL`, and `AUG_INDUSTRIAL`. `scale_jitter=False` disables the independent resize/crop branch. Keypoint models must use CPU/Albumentations; Kornia keypoint transforms are unsupported. Horizontal keypoint flips require safe left/right pairs; an empty pair list disables horizontal flips in keypoint mode.

## Checkpoints and resume

| Artifact | State | Use |
| --- | --- | --- |
| `last.ckpt`, `checkpoint_<epoch>.ckpt` | Full Lightning model, optimizer, scheduler, epoch/loop state | `resume=` for continuity |
| `checkpoint_best_regular.pth` | Best raw-weight lightweight checkpoint; no optimizer/scheduler | inference, deployment, or cold continuation |
| `checkpoint_best_ema.pth`, `last_ema.pth` | EMA lightweight checkpoints; no optimizer/scheduler | inference or cold continuation when EMA is desired |
| `checkpoint_best_total.pth` | Lightweight final best selection, model metadata, and callback state when present | default inference/deployment checkpoint |
| `metrics.csv` | CSVLogger history | inspect curves |
| `training_config.json` | high-level reproducibility record | reproduce config/class names |

Use `resume=".../last.ckpt"` when optimizer/scheduler continuity matters. A lightweight `.pth` resumes weights and epoch metadata but starts optimizer and scheduler cold; callback state requires matching callback configuration and may be absent in older files. Best-score tracking additionally expects `output_dir` to be the original checkpoint directory. To start a new fine-tune from best weights, pass `pretrain_weights=".../checkpoint_best_total.pth"` at construction instead of `resume=`.

## Loggers and callbacks

CSVLogger is always enabled in training mode. TensorBoard is enabled by default; missing/incompatible TensorBoard becomes a warning and CSV-only logging. W&B and MLflow need `rfdetr[loggers]` plus `wandb=True` / `mlflow=True`; `project` and `run` name them. `clearml=True` currently raises `NotImplementedError`; initialize the ClearML SDK before training and omit that flag.

Built-in callbacks include EMA, drop-path scheduling, periodic/latest checkpoints, COCO metrics, best-model selection, and optional early stopping. Detection monitors box mAP (`val/mAP_50_95`), segmentation monitors mask mAP (`val/segm_mAP_50_95`), and keypoint preview monitors COCO keypoint AP (`val/keypoint_map_50_95`). With `eval_ema_only=True`, real scores route to `val/ema_*` keys and corresponding regular keys can be absent.

## Custom Lightning API

```python
from rfdetr.config import RFDETRSmallConfig, TrainConfig
from rfdetr.training import RFDETRDataModule, RFDETRModelModule, build_trainer

mc = RFDETRSmallConfig(num_classes=3)
tc = TrainConfig(
    dataset_file="roboflow",
    dataset_dir="data/detection",
    output_dir="outputs/custom",
    epochs=50,
    batch_size=4,
    grad_accum_steps=4,
    tensorboard=False,
)
module = RFDETRModelModule(mc, tc)
data = RFDETRDataModule(mc, tc)
trainer = build_trainer(tc, mc, fast_dev_run=2)
trainer.fit(module, data, ckpt_path=tc.resume or None)
```

Datasets are built lazily by `setup("fit"|"validate"|"test"|"predict")`. `RFDETRDataModule` derives `pin_memory`, `persistent_workers`, and `prefetch_factor` from `TrainConfig`. Passing `callbacks=` to `build_trainer` replaces defaults; append to `trainer.callbacks` to extend them. Detection/segmentation use Lightning-owned accumulation and clipping; keypoint manual optimization owns both, so trainer-level overrides are ignored with a warning.

## Distributed training

For the high-level API, place `model.train(...)` in a script and launch:

```bash
torchrun --nproc_per_node=4 train.py
```

Inside the script, set `devices="auto"` or `devices=4` and usually `strategy="ddp"`. The default `devices=1` can leave a multi-process launch effectively using one device. Effective batch includes GPU count.

For the custom API, pass the same fields through `TrainConfig` or `build_trainer(..., strategy="ddp", devices="auto")`. RF-DETR wraps DDP with `find_unused_parameters=True` for detection, segmentation, and keypoint models. Interactive `ddp_spawn`/`ddp_notebook` use a spawn launcher. Keypoints support DDP and multi-node DDP, but not FSDP/DeepSpeed; for throughput, keep keypoint `grad_accum_steps=1` on multi-GPU because manual optimization synchronizes every microbatch. EMA is disabled automatically for sharded strategies.
