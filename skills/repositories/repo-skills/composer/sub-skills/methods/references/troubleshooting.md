# Composer methods troubleshooting

Use this file when a method import succeeds but training behavior, tensor shapes, method ordering, or in-place mutation is wrong.

## Batch shape and key failures

### Symptom: `MixUp`, `CutMix`, or `LabelSmoothing` reads the wrong tensor

Likely causes:

- The dataloader returns a dict or custom object but the algorithm still uses tuple defaults `input_key=0`, `target_key=1`.
- A nested batch requires custom getter/setter functions.
- The key identifies metadata or sample ids instead of a tensor.

Fix:

```python
from composer.algorithms import CutMix, LabelSmoothing, MixUp

algorithms = [
    MixUp(alpha=0.2, input_key="image", target_key="class_id"),
    CutMix(alpha=1.0, input_key="image", target_key="class_id"),
    LabelSmoothing(smoothing=0.1, target_key="class_id"),
]
```

For nested structures, pass `(getter, setter)` and ensure the setter returns the updated batch:

```python
def get_x(batch):
    return batch["features"]["image"]

def set_x(batch, value):
    batch["features"]["image"] = value
    return batch

mixup = MixUp(input_key=(get_x, set_x), target_key="class_id")
```

### Symptom: `CutMix` raises or silently produces unusable images

Check:

- `CutMix` and `cutmix_batch` expect image-like input shaped `(N, C, H, W)`.
- Tiny spatial sizes can produce clipped or zero-sized boxes, making the augmentation weak.
- Segmentation-style targets with spatial dimensions are handled differently from class-index targets; do not use `interpolate_loss=True` when target has the same spatial dimensions as input.

### Symptom: `LabelSmoothing` shape mismatch

Check:

- `smooth_labels(logits, target, smoothing=0.1)` infers class count from `logits.shape[1]`.
- `logits` should be shaped `(N, num_classes, ...)`.
- Integer targets should be shaped `(N, ...)`; dense/one-hot targets should match `logits` shape.
- If the loss does not accept dense/probability targets, use a compatible soft-target loss or keep loss interpolation with methods that support it.

## `num_classes` and older functional snippets

Composer 0.33.0.dev0 uses `mixup_batch`, `cutmix_batch`, and `smooth_labels` signatures that do not take a `num_classes=` keyword. If older code fails with `unexpected keyword argument 'num_classes'`, remove that argument.

For custom loops, class count is still needed whenever you manually convert integer labels to one-hot labels. Derive it from model outputs or pass it to your own `torch.nn.functional.one_hot(..., num_classes=num_classes)` call. `smooth_labels` avoids a separate `num_classes` argument by using `logits.shape[1]`.

## Functional API at the wrong stage

Functional helpers do not register with Composer events. The caller must place them correctly:

- Dataset transforms: `augmix_image` and `randaugment_image` before `DataLoader` batching.
- Batch input changes: `mixup_batch`, `cutmix_batch`, `colout_batch`, `cutout_batch`, `resize_batch`, and `set_batch_sequence_length` after loading a batch and before the forward pass that consumes the changed inputs.
- Target changes: `smooth_labels` after logits are available and before loss; MixUp/CutMix target or loss interpolation before loss/backward.
- Gradient clipping: after `loss.backward()` and before `optimizer.step()`.
- EMA: after optimizer updates according to the selected update interval.
- Model surgery: before optimizer construction when possible.

If the method requires several stages, use the algorithm class. For example, `MixUp(interpolate_loss=False)` modifies inputs before forward and targets before loss; `MixUp(interpolate_loss=True)` modifies inputs before forward and loss before backward.

## Model surgery does not find matching modules

Symptoms:

- A no-effect warning is emitted.
- Layer counts do not change.
- Speed or accuracy does not change after adding a method.

Common causes and fixes:

- `BlurPool` only replaces strided `Conv2d` and eligible `MaxPool2d`; lower `min_channels` only if replacing early/small convs is intended.
- `SqueezeExcite` only wraps `Conv2d` layers with enough channels; tune `min_channels`.
- `Factorize` skips layers too small or rank choices unlikely to speed up computation.
- `StochasticDepth` currently targets registered residual bottleneck classes such as `"ResNetBottleneck"`; ordinary sequential blocks are not enough.
- `GhostBatchNorm` needs `BatchNorm1d`/`BatchNorm2d`/`BatchNorm3d` modules and per-device batches at least as large as `ghost_batch_size`.
- `WeightStandardization` applies to convolution modules and may warn if symbolic tracing cannot determine last-layer ordering.
- NLP surgery (`Alibi`, `GatedLinearUnits`) requires optional NLP dependencies and supported transformer/BERT-style module classes.

Always inspect the mutated model or count replacement module class names after functional surgery. The bundled `scripts/functional_smoke.py` shows a no-download pattern.

## Optimizer stale after in-place mutation

Symptoms:

- New layers do not train.
- Optimizer parameter groups still contain parameters from replaced modules.
- Loss plateaus immediately after model surgery.

Fix:

1. Prefer applying surgery before optimizer creation.
2. If an optimizer already exists, pass it to helpers that accept `optimizers=`:

```python
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
cf.apply_blurpool(model, optimizers=optimizer)
```

3. In `Trainer`, prefer algorithm classes such as `BlurPool`, `Factorize`, `SqueezeExcite`, `GhostBatchNorm`, and `Alibi`; they receive `state.optimizers` when their event runs.
4. If a helper does not expose `optimizers=`, recreate the optimizer after mutation unless the method documentation guarantees it only changes parametrization/layout.

Checkpoint note: methods that change module structure can require the same algorithm list when loading checkpoints. `SAM` and `StochasticDepth` emit known weight-mismatch warnings in some resume paths; use the same method configuration and consider weight-only loading when resuming from incompatible checkpoints.

## Algorithm ordering and event interactions

Ordering matters most when two algorithms run on the same event or modify the same tensor/module.

- Structure/layout algorithms usually run at `INIT`. Put `ChannelsLast`, `BlurPool`, `SqueezeExcite`, `Factorize`, `StochasticDepth`, low-precision norm replacement, and NLP surgery before methods that assume a stable module layout.
- Batch algorithms that modify both inputs and targets/losses must match the loss function. Combining `MixUp`, `CutMix`, and `LabelSmoothing` can create dense targets; verify the criterion accepts them.
- Composer runs `BEFORE_*` events in list order and `AFTER_*` events in reverse order. This lets paired algorithms undo temporary state, but it also means list order can affect interactions.
- If two model-surgery methods wrap the same base module type, test each individually, inspect resulting modules, then add the second method.

## Optional dependencies and NLP methods

NLP-specific methods may fail even when core Composer imports:

- `Alibi` needs registered attention surgery policies and `max_sequence_length` sized for the longest train/eval sequence.
- `GatedLinearUnits` expects supported Hugging Face BERT-style model classes and may need a manually supplied activation function if the model has ambiguous activations.
- `SeqLengthWarmup` assumes batch tensors can be truncated/reshaped according to sequence-length conventions.

Install public dependencies such as `pip install "mosaicml[nlp]"` or `pip install transformers` in the runtime environment when these methods are required.

## GPU-only or long-training assumptions

A CPU random-tensor smoke can prove method plumbing, not speedup.

- `ChannelsLast`, low-precision norm replacement, and many convolution methods usually show throughput effects on GPU/AMP workloads, not small CPU loops.
- `SAM` can roughly double per-step compute on intervals where it runs because it needs two closure evaluations.
- `SelectiveBackprop`, `ProgressiveResizing`, and `StochasticDepth` can make dataloading or small-batch overhead the bottleneck.
- `GyroDropout` examples are long-training/GPU-oriented; use a small synthetic smoke only to check import and mutation behavior.

Route distributed scaling, FSDP, and launcher diagnosis to `../distributed/SKILL.md`; route logging/profiling interpretation to `../observability/SKILL.md`.
