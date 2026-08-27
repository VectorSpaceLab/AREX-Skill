# Training Workflows

This reference gives compact SMP loss/metric loop patterns. For model construction details, use [model-building](../../model-building/SKILL.md). For encoder-specific normalization, use [encoders-preprocessing](../../encoders-preprocessing/SKILL.md). For saving/exporting, use [model-export](../../model-export/SKILL.md).

## General Loop Contract

- Keep model heads unactivated (`activation=None`) during training unless you intentionally want losses to receive probabilities.
- Move `images` and `masks` to the same device as the model before the forward pass.
- Use floating image tensors; use long integer masks for multiclass targets and binary `0/1` masks for binary/multilabel targets.
- Call `model.train()` for optimizer steps and `model.eval()` plus `torch.inference_mode()` for validation.
- Run metrics on detached predictions; do not backpropagate through `get_stats`.

## Binary Segmentation

Binary foreground/background segmentation uses one output channel.

```python
import torch
import segmentation_models_pytorch as smp

mode = smp.losses.BINARY_MODE
loss_fn = smp.losses.DiceLoss(mode=mode, from_logits=True)

def train_step(model, batch, optimizer, device):
    model.train()
    images, masks = batch
    images = images.to(device, dtype=torch.float32)
    masks = masks.to(device).long()
    if masks.ndim == 3:
        masks = masks.unsqueeze(1)

    optimizer.zero_grad(set_to_none=True)
    logits = model(images)              # (N, 1, H, W)
    loss = loss_fn(logits, masks)       # target may be (N, 1, H, W)
    loss.backward()
    optimizer.step()
    return float(loss.detach().cpu())
```

Binary validation with metrics:

```python
@torch.inference_mode()
def validate_binary(model, dataloader, device):
    model.eval()
    total_tp = total_fp = total_fn = total_tn = None
    for images, masks in dataloader:
        images = images.to(device, dtype=torch.float32)
        masks = masks.to(device).long()
        if masks.ndim == 3:
            masks = masks.unsqueeze(1)
        logits = model(images)
        probs = logits.sigmoid()
        tp, fp, fn, tn = smp.metrics.get_stats(
            probs, masks, mode="binary", threshold=0.5
        )
        totals = [value.sum(dim=0) for value in (tp, fp, fn, tn)]
        if total_tp is None:
            total_tp, total_fp, total_fn, total_tn = totals
        else:
            total_tp += totals[0]; total_fp += totals[1]
            total_fn += totals[2]; total_tn += totals[3]

    iou = smp.metrics.iou_score(total_tp, total_fp, total_fn, total_tn, reduction="micro")
    f1 = smp.metrics.f1_score(total_tp, total_fp, total_fn, total_tn, reduction="micro")
    return {"iou": float(iou), "f1": float(f1)}
```

## Multiclass Segmentation

Multiclass segmentation uses one channel per class and a single integer class id per pixel.

```python
mode = smp.losses.MULTICLASS_MODE
loss_fn = smp.losses.SoftCrossEntropyLoss(smooth_factor=0.05, ignore_index=255)
# Alternative overlap loss:
# loss_fn = smp.losses.DiceLoss(mode=mode, from_logits=True, ignore_index=255)

def train_multiclass_step(model, batch, optimizer, device):
    images, masks = batch
    images = images.to(device, dtype=torch.float32)
    masks = masks.to(device).long()     # (N, H, W), values 0..C-1 or ignore_index

    optimizer.zero_grad(set_to_none=True)
    logits = model(images)              # (N, C, H, W)
    loss = loss_fn(logits, masks)
    loss.backward()
    optimizer.step()
    return float(loss.detach().cpu())
```

Multiclass metrics require class-id predictions, not logits:

```python
@torch.inference_mode()
def multiclass_stats(logits, masks, classes, ignore_index=None):
    pred = logits.argmax(dim=1).long()  # (N, H, W)
    return smp.metrics.get_stats(
        pred,
        masks.long(),
        mode="multiclass",
        num_classes=classes,
        ignore_index=ignore_index,
    )
```

Do not pass `threshold` in multiclass mode.

## Multilabel Segmentation

Multilabel segmentation uses one independent binary channel per class.

```python
mode = smp.losses.MULTILABEL_MODE
loss_fn = smp.losses.FocalLoss(mode=mode, from_logits=True, gamma=2.0)
# Common composite alternative:
# dice_loss = smp.losses.DiceLoss(mode=mode, from_logits=True)
# bce_loss = smp.losses.SoftBCEWithLogitsLoss()
# loss = dice_loss(logits, masks) + bce_loss(logits, masks)

def train_multilabel_step(model, batch, optimizer, device):
    images, masks = batch
    images = images.to(device, dtype=torch.float32)
    masks = masks.to(device, dtype=torch.float32)  # (N, C, H, W), each channel 0/1

    optimizer.zero_grad(set_to_none=True)
    logits = model(images)                         # (N, C, H, W)
    loss = loss_fn(logits, masks)
    loss.backward()
    optimizer.step()
    return float(loss.detach().cpu())
```

Multilabel metrics require a threshold when using probabilities:

```python
@torch.inference_mode()
def multilabel_scores(logits, masks):
    probs = logits.sigmoid()
    tp, fp, fn, tn = smp.metrics.get_stats(
        probs,
        masks.long(),
        mode="multilabel",
        threshold=0.5,
    )
    return {
        "iou_micro": float(smp.metrics.iou_score(tp, fp, fn, tn, reduction="micro")),
        "f1_macro": float(smp.metrics.f1_score(tp, fp, fn, tn, reduction="macro")),
    }
```

## Tiny Smoke Workflow

Before launching real training, run one CPU batch with random tensors and no pretrained downloads:

```python
import torch
import segmentation_models_pytorch as smp

model = smp.Unet(
    encoder_name="resnet18",
    encoder_weights=None,
    in_channels=3,
    classes=1,
)
images = torch.randn(2, 3, 64, 64)
masks = torch.randint(0, 2, (2, 1, 64, 64)).long()
logits = model(images)
loss = smp.losses.DiceLoss(smp.losses.BINARY_MODE, from_logits=True)(logits, masks)
assert logits.shape == masks.shape
assert torch.isfinite(loss)
```

Use the bundled validator for loss/metric-only checks that avoid model construction:

```bash
python sub-skills/training-evaluation/scripts/validate_training_shapes.py --mode multiclass --classes 3 --loss dice
```

## Adapting Examples Safely

- Replace dataset downloads with a tiny synthetic batch when only validating loop wiring.
- Set `encoder_weights=None` for smoke tests to avoid network access; switch to pretrained weights only when the environment already has them or downloads are explicitly intended.
- Keep image preprocessing consistent with the selected encoder; see [encoders-preprocessing](../../encoders-preprocessing/SKILL.md).
- Choose `classes=1` for binary, `classes=C` for multiclass/multilabel, and ensure the loss mode matches that choice.
