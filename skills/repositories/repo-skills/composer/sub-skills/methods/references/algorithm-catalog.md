# Composer method catalog

This catalog groups the public `composer.algorithms` method exports and their `composer.functional` counterparts where available. Use the class form in `Trainer(algorithms=[...])` for standard Composer recipes; use the functional form only when a custom PyTorch loop owns the placement contract.

## Data augmentations

These operate on image samples or transform pipelines before batching.

| Method | Algorithm / helper | Functional API | Default knobs | Notes |
|---|---|---|---|---|
| AugMix | `AugMix`, `AugmentAndMixTransform` | `augmix_image` | `severity=3`, `depth=-1`, `width=3`, `alpha=1.0`, `augmentation_set="all"` | Image-preserving augmentation. Use as a transform before `DataLoader` when possible. |
| RandAugment | `RandAugment`, `RandAugmentTransform` | `randaugment_image` | `severity=9`, `depth=2`, `augmentation_set="all"` | Transform-level augmentation. Keep normalization and tensor conversion order consistent with the dataset. |

## Batch augmentations and target mixing

These require a real minibatch and are sensitive to batch structure. Defaults assume `(inputs, targets)` tuple batches unless `input_key` / `target_key` are changed.

| Method | Algorithm class | Functional API | Default knobs | Notes |
|---|---|---|---|---|
| MixUp | `MixUp(alpha=0.2, interpolate_loss=False, input_key=0, target_key=1)` | `mixup_batch(input, target, mixing=None, alpha=0.2, indices=None)` | `alpha=0.2` | Functional call returns mixed inputs, permuted targets, and mixing coefficient; caller must mix losses or dense labels. |
| CutMix | `CutMix(alpha=1.0, interpolate_loss=False, uniform_sampling=False, input_key=0, target_key=1)` | `cutmix_batch(input, target, length=None, alpha=1.0, bbox=None, indices=None, uniform_sampling=False)` | `alpha=1.0`, `uniform_sampling=False` | Requires image-like `(N, C, H, W)` input. Return value includes adjusted unmixed area and box. |
| LabelSmoothing | `LabelSmoothing(smoothing=0.1, target_key=1)` | `smooth_labels(logits, target, smoothing=0.1)` | `smoothing=0.1` | Functional helper infers class count from `logits.shape[1]`. Trainer restores original labels after loss. |
| ColOut | `ColOut(p_row=0.15, p_col=0.15, batch=True, resize_target="auto", input_key=0, target_key=1)`, `ColOutTransform` | `colout_batch(sample, p_row=0.15, p_col=0.15, resize_target="auto")` | `p_row=0.15`, `p_col=0.15` | Removes rows/columns. Can be transform-like or batch-like depending on shape and `batch`. |
| CutOut | `CutOut(num_holes=1, length=0.5, uniform_sampling=False, input_key=0)` | `cutout_batch(input, num_holes=1, length=0.5, uniform_sampling=False)` | `num_holes=1`, `length=0.5` | Randomly masks rectangular regions of image batches. |

## Model surgery and representation changes

These mutate a model in place. Prefer algorithm classes in Trainer recipes. In custom code, apply before optimizer construction or pass `optimizers=` where supported.

| Method | Algorithm class | Functional API | Default knobs | Matching constraints |
|---|---|---|---|---|
| BlurPool | `BlurPool(replace_convs=True, replace_maxpools=True, blur_first=True, min_channels=16)` | `apply_blurpool(..., optimizers=None)` | Replaces strided `Conv2d` and eligible `MaxPool2d`; skips convs with `in_channels < min_channels`. | No-op if no matching strided conv/pool layers. |
| ChannelsLast | `ChannelsLast()` | `apply_channels_last(model)` | No hyperparameters. | Sets model memory format to channels-last; speed benefit is usually GPU/conv dependent. |
| SqueezeExcite | `SqueezeExcite(latent_channels=64, min_channels=128)`, `SqueezeExcite2d`, `SqueezeExciteConv2d` | `apply_squeeze_excite(..., optimizers=None)` | Adds SE blocks after eligible `Conv2d`. | Skips convs below `min_channels`; may add overhead on small feature maps/channels. |
| StochasticDepth | `StochasticDepth(target_layer_name, stochastic_method="block", drop_rate=0.2, drop_distribution="linear", drop_warmup=0.0)` | `apply_stochastic_depth(model, target_layer_name, stochastic_method="block", drop_rate=0.2, drop_distribution="linear")` | Requires explicit `target_layer_name`; currently `"ResNetBottleneck"`. | For residual/skip architectures; can affect checkpoint compatibility. |
| Factorize | `Factorize(factorize_convs=True, factorize_linears=True, min_channels=256, latent_channels=0.25, min_features=256, latent_features=128)` | `apply_factorization(..., min_channels=512, latent_channels=0.25, min_features=512, latent_features=0.25, optimizers=None)` | Replaces eligible `Conv2d`/`Linear` with lower-rank modules. | Only useful when rank reduction can plausibly speed up the layer. |
| GhostBatchNorm | `GhostBatchNorm(ghost_batch_size=32)` | `apply_ghost_batchnorm(model, ghost_batch_size=32, optimizers=None)` | Splits batch norm statistics into chunks. | Per-device batch size must be at least `ghost_batch_size`. |
| WeightStandardization | `WeightStandardization(n_last_layers_ignore=0)` | `apply_weight_standardization(module, n_last_layers_ignore=0)` | Parametrizes conv weights. | Applies to `Conv1d`/`Conv2d`/`Conv3d`; tracing may be approximate for dynamic forwards. |
| LowPrecisionLayerNorm | `LowPrecisionLayerNorm(apply_at=Event.INIT)` | `apply_low_precision_layernorm(model, precision=None, optimizers=None)` | Only active for AMP FP16/BF16 precision. | No effect in FP32; apply only at supported load/init events. |
| LowPrecisionGroupNorm | `LowPrecisionGroupNorm(apply_at=Event.INIT)` | `apply_low_precision_groupnorm(model, precision=None, optimizers=None)` | Only active for AMP FP16/BF16 precision. | No effect in FP32; apply only at supported load/init events. |
| GatedLinearUnits | `GatedLinearUnits(act_fn=None, gated_layer_bias=False, non_gated_layer_bias=False)` | `apply_gated_linear_units(model, optimizers, act_fn=None, gated_layer_bias=False, non_gated_layer_bias=False)` | Swaps BERT feed-forward blocks for gated blocks. | Requires NLP dependencies and supported Hugging Face BERT-style modules. |
| Alibi | `Alibi(max_sequence_length, train_sequence_length_scaling=0.25)` | `apply_alibi(model, max_sequence_length, optimizers=None)` | Removes position embeddings / attention surgery and may reshape dict batches. | Requires NLP dependencies and registered attention module policies. |
| GyroDropout | `GyroDropout(p=0.5, sigma=256, tau=16)` | `apply_gyro_dropout(model, iters_per_epoch, max_epoch, p, sigma, tau)` | Replaces dropout layers with gyro dropout schedule. | Long-training and GPU-oriented; use the algorithm unless the custom loop tracks epochs/steps. |

## Training-loop modifications

These change what happens over time inside the loop. Functional primitives exist for some, but the algorithm class is the safer default because it owns timing.

| Method | Algorithm class | Functional API | Default knobs | Stage concerns |
|---|---|---|---|---|
| LayerFreezing | `LayerFreezing(freeze_start=0.5, freeze_level=1.0)` | `freeze_layers(model, optimizers, current_duration, freeze_start=0.5, freeze_level=1.0)` | Starts at 50% duration; can freeze up to all eligible layers. | Removes frozen parameters from optimizers; schedule needs elapsed duration. |
| ProgressiveResizing | `ProgressiveResizing(mode="resize", initial_scale=0.5, finetune_fraction=0.2, delay_fraction=0.5, size_increment=4, resize_targets=False, input_key=0, target_key=1)` | `resize_batch(input, target, scale_factor, mode="resize", resize_targets=False)` | Starts smaller, then returns to full size. | Batch/image shape and target resizing must match task type. |
| SelectiveBackprop | `SelectiveBackprop(start=0.5, end=0.9, keep=0.5, scale_factor=1.0, interrupt=2, input_key=0, target_key=1)` | `should_selective_backprop(...)`, `select_using_loss(...)` | Keeps 50% of examples during the active window. | Needs model/loss evaluation to select examples and can shift data-loading bottlenecks. |
| SeqLengthWarmup | `SeqLengthWarmup(duration=0.3, min_seq_length=8, max_seq_length=1024, step_size=8, truncate=True, preserve_end_of_sequence=False)` | `set_batch_sequence_length(batch, curr_seq_len, truncate=True, preserve_end_of_sequence=False)` | NLP sequence length grows over early training. | Batch shape convention must match the NLP model/dataloader. |
| NoOpModel | `NoOpModel()` | none | No hyperparameters. | Replaces the model with a dummy model for dataloader/profiling workflows; route profiling interpretation to observability. |

## Precision, optimizer, and scheduler-adjacent methods

These are not ordinary batch transforms. They usually need optimizer state, precision state, scheduler state, or a closure-capable Trainer loop.

| Method | Public surface | Functional API | Default knobs | Notes |
|---|---|---|---|---|
| GradientClipping | `GradientClipping(clipping_type, clipping_threshold)` | `apply_gradient_clipping(model, clipping_type, clipping_threshold, fsdp_enabled)` | Required `clipping_type` and threshold. | Runs after backward before optimizer step; FSDP changes implementation details. |
| SAM | `SAM(rho=0.05, epsilon=1.0e-12, interval=1)`, `SAMOptimizer` | none | Runs every step by default; each SAM step is roughly two forward/backward passes. | Wraps existing optimizers at `AFTER_LOAD`; requires closure support. |
| EMA | `EMA(half_life="1000ba", smoothing=None, ema_start="0.0dur", update_interval=None)` | `compute_ema(model, ema_model, smoothing=0.99)` | Half-life controls smoothing unless direct smoothing is set. | Maintains evaluation weights; coordinate with checkpointing/evaluation. |
| SWA | `SWA(swa_start="0.7dur", swa_end="0.97dur", update_interval="1ep", schedule_swa_lr=False, anneal_strategy="linear", anneal_steps=10, swa_lr=None)` | none | Active near late training by default. | Trainer-owned averaging and optional LR scheduling. |
| Low precision norms | `LowPrecisionLayerNorm`, `LowPrecisionGroupNorm` | see model-surgery table | Apply at init/load events. | Cross-listed because they depend on AMP precision state. |
| ChannelsLast | `ChannelsLast()` | `apply_channels_last(model)` | No hyperparameters. | Cross-listed because throughput impact is precision/device/layout dependent. |
| Decoupled weight decay | `composer.optim.DecoupledAdamW`, `composer.optim.DecoupledSGDW` | optimizer classes, not algorithms | Optimizer-specific. | Use through optimizer selection; route optimizer construction details to `../training/SKILL.md`. |
| Scale schedule | `Trainer(scale_schedule_ratio=...)` | none | Default ratio `1.0`. | Scheduler/budget method, not an algorithm export; route Trainer/scheduler wiring to `../training/SKILL.md`. |

## Ordering heuristics for recipes

- Put structure/layout surgery methods early in the algorithm list: `ChannelsLast`, `BlurPool`, `SqueezeExcite`, `Factorize`, `StochasticDepth`, low-precision norm replacement.
- Put batch/label methods together and verify the loss supports their target representation: `MixUp`, `CutMix`, `LabelSmoothing`, `ColOut`, `CutOut`.
- Put optimizer/loop methods only after the optimizer and duration semantics are clear: `SAM`, `SWA`, `EMA`, `GradientClipping`, `LayerFreezing`, `SelectiveBackprop`, `ProgressiveResizing`.
- Algorithms on the same event can interact. If two surgeries wrap the same module type, try each alone first and inspect whether both replacements happened.
