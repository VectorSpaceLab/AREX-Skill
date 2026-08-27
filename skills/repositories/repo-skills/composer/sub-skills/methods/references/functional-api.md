# Composer functional API contracts

Composer exposes most speedup methods in two forms:

- `composer.algorithms.<ClassName>` for `Trainer(algorithms=[...])` recipes.
- `composer.functional.<function_name>` for custom PyTorch loops or explicit pre-training model surgery.

Install the public package with `pip install mosaicml` when the package is not already available.

## Choosing the surface

Use algorithm classes when:

- The training loop is Composer `Trainer`.
- The method needs lifecycle events such as `INIT`, `BEFORE_FORWARD`, `BEFORE_LOSS`, `AFTER_LOSS`, `BEFORE_BACKWARD`, `AFTER_LOAD`, or `BATCH_START`.
- The method mutates the model and an optimizer may already exist; Trainer passes `state.optimizers` to surgery methods that support optimizer rebinding.
- Multiple algorithms must compose as a recipe and event ordering matters.

Use functional helpers when:

- The loop is a plain PyTorch loop and you control exactly where the method runs.
- You want a small isolated smoke test for one method.
- You can apply model surgery before constructing the optimizer, or can pass existing optimizers to helpers that accept `optimizers=`.
- You are willing to implement any target interpolation, loss interpolation, schedule updates, or batch reshaping that the Trainer algorithm would otherwise own.

## Data-transform functions

These are usually inserted into dataset transforms before batching. They expect image-like inputs and may rely on PIL/torchvision-style transform conventions.

- `augmix_image(img, severity=3, depth=-1, width=3, alpha=1.0, augmentation_set="all")`
- `randaugment_image(img, severity=9, depth=2, augmentation_set="all")`

Algorithm-class counterparts:

- `AugMix(severity=3, depth=-1, width=3, alpha=1.0, augmentation_set="all")`
- `RandAugment(severity=9, depth=2, augmentation_set="all")`
- Transform classes `AugmentAndMixTransform(...)` and `RandAugmentTransform(...)` are exported for direct transform pipelines.

## Batch functions

Batch functions run after `batch = next(dataloader)` and before the forward or loss stage that consumes the changed tensors. They do not know about `State`, so they return values that the caller must thread into the loop.

### MixUp

```python
from composer import functional as cf

inputs, targets = batch
mixed_inputs, permuted_targets, mixing = cf.mixup_batch(
    inputs,
    targets,
    alpha=0.2,
)
outputs = model(mixed_inputs)
loss = (1 - mixing) * loss_fn(outputs, targets) + mixing * loss_fn(outputs, permuted_targets)
```

Contract:

- `mixup_batch(input, target, mixing=None, alpha=0.2, indices=None)`.
- `input` shape is `(minibatch, ...)`; permutation is along dimension `0`.
- Returns `(input_mixed, target_perm, mixing)`.
- If `mixing` is not provided, it is sampled from `Beta(alpha, alpha)` and folded to `<= 0.5` so the original label remains dominant.
- Algorithm class: `MixUp(alpha=0.2, interpolate_loss=False, input_key=0, target_key=1)`.
- With `interpolate_loss=False`, Trainer interpolates dense targets before loss; with `interpolate_loss=True`, Trainer interpolates losses before backward and requires a callable `model.loss` or `model.module.loss`.

### CutMix

```python
from composer import functional as cf

inputs, targets = batch
mixed_inputs, permuted_targets, keep_area, bbox = cf.cutmix_batch(
    inputs,
    targets,
    alpha=1.0,
    uniform_sampling=False,
)
outputs = model(mixed_inputs)
loss = keep_area * loss_fn(outputs, targets) + (1 - keep_area) * loss_fn(outputs, permuted_targets)
```

Contract:

- `cutmix_batch(input, target, length=None, alpha=1.0, bbox=None, indices=None, uniform_sampling=False)`.
- `input` must be image-like `(N, C, H, W)`.
- `target` may be integer class ids, one-hot/dense labels, segmentation masks, or other tensors indexed along dimension `0`.
- Returns `(input_mixed, target_perm, adjusted_lambda, bbox)` where `adjusted_lambda` is the unmixed area fraction after clipping the sampled box.
- Do not pass both `length` and `bbox`.
- Algorithm class: `CutMix(alpha=1.0, interpolate_loss=False, uniform_sampling=False, input_key=0, target_key=1)`.

### Label smoothing

```python
from composer import functional as cf

outputs = model(inputs)                 # shape: (N, num_classes, ...)
smoothed_targets = cf.smooth_labels(outputs, targets, smoothing=0.1)
loss = loss_fn(outputs, smoothed_targets)
```

Contract:

- `smooth_labels(logits, target, smoothing=0.1)`.
- `logits` shape must be `(N, num_classes, ...)`; `num_classes` is inferred from `logits.shape[1]`.
- `target` can be integer class ids with shape `(N, ...)` or dense/one-hot labels with the same shape as `logits`.
- Algorithm class: `LabelSmoothing(smoothing=0.1, target_key=1)`.
- The Trainer algorithm smooths targets at `BEFORE_LOSS` and restores original targets at `AFTER_LOSS`.

### Other batch helpers

- `colout_batch(sample, p_row=0.15, p_col=0.15, resize_target="auto")`; algorithm `ColOut(p_row=0.15, p_col=0.15, batch=True, resize_target="auto", input_key=0, target_key=1)`.
- `cutout_batch(input, num_holes=1, length=0.5, uniform_sampling=False)`; algorithm `CutOut(num_holes=1, length=0.5, uniform_sampling=False, input_key=0)`.
- `resize_batch(input, target, scale_factor, mode="resize", resize_targets=False)`; scheduled algorithm `ProgressiveResizing(mode="resize", initial_scale=0.5, finetune_fraction=0.2, delay_fraction=0.5, size_increment=4, resize_targets=False, input_key=0, target_key=1)`.
- `set_batch_sequence_length(batch, curr_seq_len, truncate=True, preserve_end_of_sequence=False)`; scheduled NLP algorithm `SeqLengthWarmup(duration=0.3, min_seq_length=8, max_seq_length=1024, step_size=8, truncate=True, preserve_end_of_sequence=False)`.

## Trainer batch-key semantics

For algorithm classes, `input_key` and `target_key` tell Composer how to read and write parts of `state.batch`.

- Integer keys index tuple/list batches: default `(inputs, targets)` means `input_key=0`, `target_key=1`.
- String keys index dict batches: `input_key="image"`, `target_key="label"`.
- A `(getter, setter)` pair supports custom/nested batch objects. The getter is called as `getter(batch)`. The setter is called as `setter(batch, value)` and must return the updated batch.

Dict-shaped batch example:

```python
from composer.algorithms import MixUp

mixup = MixUp(alpha=0.2, input_key="x", target_key="y")
# Dataloader yields {"x": images, "y": labels, "meta": sample_ids}
trainer = Trainer(..., algorithms=[mixup])
```

Nested batch example:

```python
def get_image(batch):
    return batch["features"]["image"]

def set_image(batch, value):
    batch["features"]["image"] = value
    return batch

mixup = MixUp(alpha=0.2, input_key=(get_image, set_image), target_key="class_id")
```

## Model-surgery functions

Model-surgery helpers mutate the model in place. Apply them before optimizer construction whenever possible.

```python
from composer import functional as cf

model = build_model()
cf.apply_channels_last(model)
cf.apply_blurpool(model, min_channels=16)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
```

If the optimizer already exists, pass it to helpers that accept `optimizers=`:

```python
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
cf.apply_blurpool(model, min_channels=16, optimizers=optimizer)
```

Important helpers:

- `apply_blurpool(model, replace_convs=True, replace_maxpools=True, blur_first=True, min_channels=16, optimizers=None)`; algorithm `BlurPool(replace_convs=True, replace_maxpools=True, blur_first=True, min_channels=16)`.
- `apply_channels_last(model)`; algorithm `ChannelsLast()`.
- `apply_squeeze_excite(model, latent_channels=64, min_channels=128, optimizers=None)`; algorithm `SqueezeExcite(latent_channels=64, min_channels=128)`.
- `apply_factorization(model, factorize_convs=True, factorize_linears=True, min_channels=512, latent_channels=0.25, min_features=512, latent_features=0.25, optimizers=None)`; algorithm defaults differ: `Factorize(..., min_channels=256, min_features=256, latent_features=128)`.
- `apply_ghost_batchnorm(model, ghost_batch_size=32, optimizers=None)`; algorithm `GhostBatchNorm(ghost_batch_size=32)`.
- `apply_stochastic_depth(model, target_layer_name, stochastic_method="block", drop_rate=0.2, drop_distribution="linear")`; algorithm adds `drop_warmup=0.0` and currently targets `target_layer_name="ResNetBottleneck"`.
- `apply_weight_standardization(module, n_last_layers_ignore=0)`; algorithm `WeightStandardization(n_last_layers_ignore=0)`.
- `apply_low_precision_groupnorm(model, precision=None, optimizers=None)` and `apply_low_precision_layernorm(model, precision=None, optimizers=None)`; algorithm defaults apply at `Event.INIT` and only have effect under AMP FP16/BF16 precision.
- NLP-specific surgery: `apply_alibi(model, max_sequence_length, optimizers=None)` / `Alibi(max_sequence_length, train_sequence_length_scaling=0.25)` and `apply_gated_linear_units(model, optimizers, act_fn=None, gated_layer_bias=False, non_gated_layer_bias=False)` / `GatedLinearUnits(...)`. These require NLP optional dependencies such as `transformers` and only support registered model classes.

## Loop and optimizer functions

Some loop methods have functional primitives but are easier and safer as algorithms:

- `apply_gradient_clipping(model, clipping_type, clipping_threshold, fsdp_enabled)`; algorithm `GradientClipping(clipping_type, clipping_threshold)`.
- `freeze_layers(model, optimizers, current_duration, freeze_start=0.5, freeze_level=1.0)`; algorithm `LayerFreezing(freeze_start=0.5, freeze_level=1.0)`.
- `should_selective_backprop(current_duration, batch_idx, start=0.5, end=0.9, interrupt=2)` and `select_using_loss(input, target, model, loss_fun, keep=0.5, scale_factor=1)`; algorithm `SelectiveBackprop(start=0.5, end=0.9, keep=0.5, scale_factor=1.0, interrupt=2, input_key=0, target_key=1)`.
- `compute_ema(model, ema_model, smoothing=0.99)`; algorithm `EMA(half_life="1000ba", smoothing=None, ema_start="0.0dur", update_interval=None)`.
- `SAM(rho=0.05, epsilon=1.0e-12, interval=1)` wraps existing optimizers as `SAMOptimizer` at `AFTER_LOAD` and requires closure-capable stepping; there is no `composer.functional` SAM helper.
- `SWA(swa_start="0.7dur", swa_end="0.97dur", update_interval="1ep", schedule_swa_lr=False, anneal_strategy="linear", anneal_steps=10, swa_lr=None)` is Trainer-owned; there is no `composer.functional` SWA helper.

See also `algorithm-catalog.md` for the grouped method list and `troubleshooting.md` for common placement and mutation failures.
