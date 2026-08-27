# Optimizer and Scheduler Guide

This guide covers timm optimizer and scheduler factories for custom training code.

## Optimizer Factory

Primary API:

```python
from timm.optim import create_optimizer_v2

optimizer = create_optimizer_v2(
    model,
    opt='adamw',
    lr=1e-3,
    weight_decay=0.05,
    momentum=0.9,
    foreach=None,
    filter_bias_and_bn=True,
    fallback_list=(),
    layer_decay=None,
)
```

Important parameters:

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `model_or_params` | `nn.Module`, iterable of parameters, or parameter groups | Pass the model when you want timm to create weight-decay or layer-decay groups. Pass groups only when you own all grouping logic. |
| `opt` | Optimizer registry name | Common names include `sgd`, `adam`, `adamw`, `rmsprop`, `rmsproptf`, `lamb`, `lion`, `adan`, and fused/variant names when available. |
| `lr` | Base learning rate | Required for predictable recipes even if the optimizer has a default. |
| `weight_decay` | Weight decay value | With a model and `filter_bias_and_bn=True`, biases and 1D/norm parameters are separated into no-decay groups. |
| `momentum` | Momentum-like value | Used only by optimizers that accept momentum. |
| `foreach` | Multi-tensor implementation toggle | Leave `None` unless debugging backend/device-specific optimizer issues. |
| `filter_bias_and_bn` | Exclude bias and norm/1D params from decay | Keep `True` for most vision recipes using weight decay. |
| `fallback_list` | Name patterns that use fallback optimizer groups in hybrid optimizers | Useful for optimizers such as Muon-style hybrids where some params should use AdamW fallback. |
| `fallback_no_weight_decay` | Add model `no_weight_decay()` names to fallback matching | Use when no-decay params also need fallback optimizer handling. |
| `layer_decay` | Per-layer LR scale | Use mainly for transformer/ConvNeXt-style finetuning with model layer metadata. |
| `param_group_fn` | Custom group builder | Takes precedence over timm grouping. Use only when default grouping cannot express the recipe. |

Grouping precedence when a model is passed:

1. `param_group_fn` controls all groups.
2. `layer_decay` creates layer-wise groups.
3. Positive `weight_decay` with `filter_bias_and_bn=True` creates decay/no-decay groups.
4. Otherwise all trainable parameters are in a single group.

## Config-to-Optimizer Translation

`optimizer_kwargs(cfg)` converts an argparse/config-like object to factory kwargs. It reads:

- Always: `opt`, `lr`, `weight_decay`, `momentum`.
- Optional: `opt_eps`, `opt_betas`, `layer_decay`, `layer_decay_min_scale`, `layer_decay_no_opt_scale`, `opt_args`, `opt_foreach`.

Use it when mirroring train-script-style config objects without copying every field manually:

```python
from timm.optim import create_optimizer_v2, optimizer_kwargs

optimizer = create_optimizer_v2(model, **optimizer_kwargs(args))
```

## Parameter Group Safety Checks

Before a long run, inspect groups:

```python
seen = sum(p.numel() for group in optimizer.param_groups for p in group['params'])
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
assert seen == trainable
for idx, group in enumerate(optimizer.param_groups):
    print(idx, group.get('lr'), group.get('weight_decay'), len(group['params']))
```

If `layer_decay` creates too many or too few groups, check whether the model exposes layer grouping metadata. If not, pass a deliberate `param_group_fn` or remove `layer_decay` rather than assuming timm inferred architecture depth correctly.

## Scheduler Factory

Primary API:

```python
from timm.scheduler import create_scheduler_v2

lr_scheduler, adjusted_epochs = create_scheduler_v2(
    optimizer,
    sched='cosine',
    num_epochs=100,
    decay_epochs=30,
    warmup_epochs=5,
    min_lr=1e-6,
    step_on_epochs=True,
    updates_per_epoch=0,
)
```

Supported scheduler names:

| `sched` | Scheduler | Notes |
| --- | --- | --- |
| `cosine` | `CosineLRScheduler` | Common default; supports warmup, cycles, `k_decay`, LR noise, and min LR. |
| `tanh` | `TanhLRScheduler` | Hyperbolic tangent schedule with warmup/cycles. |
| `step` | `StepLRScheduler` | Decays every `decay_epochs` by `decay_rate`. |
| `multistep` | `MultiStepLRScheduler` | Decays at `decay_milestones`. |
| `plateau` | `PlateauLRScheduler` | Epoch-stepped only; requires a validation metric in `step`. |
| `poly` | `PolyLRScheduler` | Polynomial decay; `decay_rate` is used as polynomial power. |

Factory behavior:

- Returns `(lr_scheduler, num_epochs)` where `num_epochs` may be adjusted for cycle length, cooldown, or warmup prefix.
- Converts epoch units to update units when `step_on_epochs=False`.
- Asserts `updates_per_epoch > 0` when update-stepping.
- Asserts plateau scheduling is epoch-stepped.

## Epoch-Step vs Update-Step

Epoch-stepped schedule:

```python
scheduler, num_epochs = create_scheduler_v2(
    optimizer,
    sched='cosine',
    num_epochs=100,
    warmup_epochs=5,
    step_on_epochs=True,
)
for epoch in range(num_epochs):
    train_one_epoch(...)
    validate(...)
    scheduler.step(epoch + 1)
```

Update-stepped schedule:

```python
scheduler, num_epochs = create_scheduler_v2(
    optimizer,
    sched='cosine',
    num_epochs=100,
    warmup_epochs=5,
    step_on_epochs=False,
    updates_per_epoch=len(loader),
)
num_updates = 0
for epoch in range(num_epochs):
    for batch in loader:
        train_one_batch(...)
        num_updates += 1
        scheduler.step_update(num_updates)
```

Do not mix `scheduler.step(epoch)` once per epoch with a scheduler created for update steps. That silently stretches or compresses warmup and decay by `updates_per_epoch`.

## Warmup, Noise, Cycles, and Plateau

| Feature | Parameters | Guidance |
| --- | --- | --- |
| Warmup | `warmup_epochs`, `warmup_lr`, `warmup_prefix` | `warmup_prefix=True` makes the main schedule start after warmup; otherwise warmup is part of the schedule horizon. |
| Minimum LR | `min_lr` | Use with cosine/tanh/poly/plateau to avoid decaying to zero. |
| Decay | `decay_epochs`, `decay_milestones`, `decay_rate` | Meaning depends on scheduler: interval, milestone list, multiplicative factor, or polynomial power. |
| Cycles | `cycle_mul`, `cycle_decay`, `cycle_limit` | Applies to cycle-capable schedules; adjusted epoch count reflects cycle length and cooldown. |
| Noise | `noise`, `noise_pct`, `noise_std`, `noise_seed` | Applies stochastic LR noise where supported; ranges are scaled by total schedule horizon. |
| Plateau | `plateau_mode`, `patience_epochs` | Call `scheduler.step(epoch, metric=validation_metric)` and keep `step_on_epochs=True`. |

## Hyperparameter Tags

The hparams reference maps pretrained tag families to optimizer/scheduler/loss tendencies. Examples:

- `a1`/`a2`/`a3`: LAMB with BCE loss and cosine warmup.
- `b1`/`b2`/`ra`/`ra2`/`ra3`: RMSProp-TF-style recipes, EMA, and step/exponential schedules with warmup.
- `c`/`ch`: SGD/Nesterov with AGC and cosine warmup.
- `d`/`d1`/`d2`: AdamW with BCE loss and cosine warmup.
- `sw`: AdamW with gradient clipping, EMA, and cosine warmup for transformer-like recipes.
- `am`/`ram`: SGD/Nesterov with JSD loss and cosine warmup for AugMix-style recipes.

Treat tags as starting points, not exact reproducibility guarantees. Always scale LR for effective global batch size and validate loss/target compatibility with the data pipeline.
