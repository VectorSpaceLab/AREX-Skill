# Training API Composition

This reference distills timm training building blocks for custom Python loops. It focuses on composable APIs, not train script flag catalogs.

## Minimal Training Skeleton

```python
import torch
from timm import create_model
from timm.loss import LabelSmoothingCrossEntropy
from timm.optim import create_optimizer_v2
from timm.scheduler import create_scheduler_v2
from timm.utils import AverageMeter, ModelEmaV3, accuracy

model = create_model('resnet18', pretrained=False, num_classes=10)
optimizer = create_optimizer_v2(model, opt='adamw', lr=1e-3, weight_decay=0.05)
scheduler, num_epochs = create_scheduler_v2(optimizer, sched='cosine', num_epochs=5, warmup_epochs=1)
criterion = LabelSmoothingCrossEntropy(smoothing=0.1)
model_ema = ModelEmaV3(model, decay=0.9999)

for epoch in range(num_epochs):
    model.train()
    output = model(images)
    loss = criterion(output, labels)
    loss.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    model_ema.update(model, step=epoch)
    scheduler.step(epoch + 1)
```

Use the scheduler guide before changing where `scheduler.step(...)` is called; timm schedulers can be epoch-stepped or update-stepped.

## Loss Selection

| Loss | Target form | Typical use | Notes |
| --- | --- | --- | --- |
| `torch.nn.CrossEntropyLoss` | integer class ids `[B]` | Plain classification | Good default when no soft labels or smoothing are needed. |
| `LabelSmoothingCrossEntropy(smoothing=...)` | integer class ids `[B]` | Classification with label smoothing | Asserts `smoothing < 1.0`; internally mixes hard-label NLL with uniform smoothing. |
| `SoftTargetCrossEntropy()` | soft class probabilities `[B, C]` | Mixup/CutMix or other soft-label augmentation | Targets must already be probability-like class distributions matching output shape. |
| `BinaryCrossEntropy(...)` | integer class ids or dense targets `[B, C]` | BCE-style ImageNet recipes, multi-label style heads, or mixup-compatible BCE | If target shape differs from logits, integer labels are one-hot expanded with optional smoothing. `target_threshold` can harden soft targets. |
| `JsdCrossEntropy(num_splits=3, smoothing=...)` | integer class ids for split batch | AugMix/JSD recipes | Output batch must be divisible by `num_splits`; CE is computed on the clean split and JSD over all splits. |

Common routing rules:

- Use `LabelSmoothingCrossEntropy` for hard-label classification with smoothing but no mixup/cutmix soft targets.
- Use `SoftTargetCrossEntropy` when augmentation produces dense class distributions.
- Use `BinaryCrossEntropy` when the recipe intentionally trains independent class logits, especially BCE-tagged hparam families.
- Use `JsdCrossEntropy` only when the input pipeline creates clean/augmented splits for AugMix-style batches.

## Task Wrappers

`timm.task` wraps model forward, loss computation, optional distillation, distributed preparation, compile routing, EMA state, and checkpoint state.

| API | Responsibility | Output contract |
| --- | --- | --- |
| `TrainingTask` | Base class for task objects | Forward results should contain at least `loss`; `output` is recommended for metrics. |
| `ClassificationTask(model, criterion, ...)` | Standard supervised classification | Returns `{'loss': loss, 'output': logits}`. |
| `DistillationTeacher(...)` | Teacher wrapper for logit or feature distillation | Accepts a model name or `nn.Module`, holds teacher normalization buffers, supports logits or feature extraction. |
| `LogitDistillationTask(...)` | Student logits match teacher logits plus task criterion | Returns combined loss and components for logging. |
| `FeatureDistillationTask(...)` | Student feature matching where model APIs support features | Requires compatible teacher/student feature shapes. |
| `TokenDistillationTask(...)` | Distilled-token models such as DeiT variants | Requires the student to implement `set_distilled_training(True)` and return main/distillation outputs. |

Task usage pattern:

```python
task = ClassificationTask(model, criterion)
result = task(images, labels)
loss = result['loss']
output = result['output']
```

For distillation, decide the routing first:

- **Plain classification**: no teacher, use `ClassificationTask` or direct `model + criterion`.
- **Logit KD**: teacher and student both produce compatible class logits; use `LogitDistillationTask`.
- **Feature KD**: teacher and student expose compatible feature or pre-logit representations; use `FeatureDistillationTask`.
- **Token KD**: student has a distillation token/head and `set_distilled_training`; use `TokenDistillationTask`.

## EMA Variants

| API | Use | Important behavior |
| --- | --- | --- |
| `ModelEma` | Legacy EMA helper | Deprecated; name-based state handling and resume behavior are older. |
| `ModelEmaV2` | Simpler module EMA | Deep-copies the model into `.module`, updates state values in order, and can run on a separate device. |
| `ModelEmaV3` | Current high-performance EMA | Supports `foreach`, `use_warmup`, `update_after_step`, `min_decay`, device placement, and buffer exclusion. |
| `TrainingTask.setup_ema(...)` | Task-owned EMA | Creates `ModelEmaV3` over the task trainable module and integrates with task checkpoint state. |

Initialize EMA after the model is on the intended device and before relying on checkpoint state. If EMA is stored on CPU, validation of EMA weights must explicitly move or evaluate the EMA module in a compatible environment.

## AMP Scaling and Gradient Steps

`NativeScaler(device='cuda')` wraps `torch.amp.GradScaler` where available and falls back to CUDA AMP scaler for older PyTorch. Its call signature is:

```python
loss_scaler(
    loss,
    optimizer,
    clip_grad=None,
    clip_mode='norm',
    parameters=None,
    create_graph=False,
    need_update=True,
)
```

When `clip_grad` is set, pass the same trainable parameters that the optimizer owns so the scaler can unscale before clipping. If running CPU-only smoke checks, prefer a plain `loss.backward(); optimizer.step()` path instead of constructing CUDA AMP state.

## Metrics

- `accuracy(output, target, topk=(1, 5))` returns a list of percent tensors. It clamps `maxk` to the number of classes, so top-5 on a 3-class output is treated as top-3.
- `AverageMeter` tracks `val`, `sum`, `count`, and `avg`; call `update(value, n=batch_size)` to weight batch means correctly.

Example:

```python
top1 = accuracy(output, target, topk=(1,))[0]
loss_meter.update(loss.item(), n=target.size(0))
acc_meter.update(top1.item(), n=target.size(0))
```

## Checkpoint Saver Concepts

`CheckpointSaver` tracks `last`, top-N checkpoint files, best metric, and recovery checkpoints. It saves optimizer state, optional args, optional AMP scaler state, and either direct model/EMA state or task-owned checkpoint state.

- Without a task, saved keys include `state_dict` and optionally `state_dict_ema`.
- With a task, saver calls `task.get_checkpoint_state(...)` and `task.get_checkpoint_state(ema=True, ...)` so task-owned state can be saved alongside model weights.
- Recovery checkpoints are separate from best/top-N checkpoint tracking and are intended for interruption recovery.

For task-based resume, use the task helper APIs (`resume_task_checkpoint`, `load_task_ema_checkpoint`) so `task_state` and EMA task state are restored through the task wrapper rather than loaded into the wrong module.
