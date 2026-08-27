---
name: methods
description: "Use Composer speedup methods through algorithm classes, functional
  helpers, recipes, batch-key routing, and in-place model/optimizer mutations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Composer Methods Router

Use this sub-skill when the task is to add, compose, debug, or translate MosaicML Composer speedup methods from `composer.algorithms` and `composer.functional`.

## Route first

- For Trainer construction, dataloaders, `ComposerModel`, max duration, checkpointing, and optimizer basics, route to `../training/SKILL.md`.
- For loggers, profiling, speed monitors, metric visualization, and throughput diagnosis, route to `../observability/SKILL.md`.
- For distributed launch, DDP/FSDP setup, multi-node concerns, and backend placement, route to `../distributed/SKILL.md`.
- For TorchScript/ONNX/export/inference packaging after method application, route to `../inference-export/SKILL.md`.

## Main decision: algorithm class or functional API

Prefer `composer.algorithms` classes in `Trainer(algorithms=[...])` when the user is already using Composer Trainer or wants a recipe of multiple methods. The Trainer event engine places each algorithm at the relevant event, passes `state.optimizers` to model-surgery algorithms, handles paired before/after events, and lets batch algorithms use `input_key` / `target_key` without changing the dataloader.

Use `composer.functional` when the user owns a custom PyTorch loop, wants to test one method in isolation, or needs to mutate a model before creating the optimizer. With the functional API, the caller owns exact stage placement, target/loss interpolation, optimizer rebinding after surgery, and any schedule logic.

```python
from composer import Trainer
from composer.algorithms import BlurPool, ChannelsLast, LabelSmoothing, MixUp

algorithms = [
    ChannelsLast(),
    BlurPool(replace_convs=True, replace_maxpools=True, blur_first=True, min_channels=16),
    MixUp(alpha=0.2, interpolate_loss=False, input_key="image", target_key="label"),
    LabelSmoothing(smoothing=0.1, target_key="label"),
]

trainer = Trainer(
    model=model,
    train_dataloader=train_dataloader,
    eval_dataloader=eval_dataloader,
    optimizers=optimizer,
    max_duration="10ep",
    algorithms=algorithms,
)
```

## Placement rules

1. Image transforms such as `RandAugment` or `AugMix` belong in dataset transforms before batching.
2. Batch methods such as `MixUp`, `CutMix`, `ColOut`, `CutOut`, and `LabelSmoothing` run after a batch is available and before the forward/loss stage that consumes the modified tensors.
3. Model surgery such as `BlurPool`, `SqueezeExcite`, `Factorize`, `StochasticDepth`, `Alibi`, low-precision norm replacements, and `ChannelsLast` mutates the model in place. Apply it before optimizer construction, or pass existing optimizers to functional helpers that accept `optimizers=`. Trainer algorithms do this through `state.optimizers`.
4. Loop and optimizer methods such as `LayerFreezing`, `ProgressiveResizing`, `SelectiveBackprop`, `SeqLengthWarmup`, `EMA`, `SWA`, `SAM`, and `GradientClipping` depend on event timing or optimizer state. Use algorithm classes unless the user is explicitly maintaining those stages in a custom loop.

## Batch key routing

Batch algorithms default to tuple batches: `input_key=0`, `target_key=1`. For dict batches, pass string keys instead of rewriting the dataloader:

```python
from composer.algorithms import CutMix, MixUp, LabelSmoothing

algorithms = [
    MixUp(alpha=0.2, input_key="image", target_key="label"),
    CutMix(alpha=1.0, uniform_sampling=False, input_key="image", target_key="label"),
    LabelSmoothing(smoothing=0.1, target_key="label"),
]
```

For nested or custom batch objects, pass `(getter, setter)` callables. The getter receives the batch and returns the tensor; the setter receives `(batch, value)` and returns the updated batch.

## References and bundled smoke

- `references/functional-api.md`: function families, stage contracts, batch-key semantics, and custom-loop recipes.
- `references/algorithm-catalog.md`: exported Composer method list grouped by taxonomy.
- `references/troubleshooting.md`: method-specific failure modes and fixes.
- `scripts/functional_smoke.py`: no-download random tensor smoke for a batch method plus functional model surgery.

Run the smoke from this sub-skill directory with:

```bash
python scripts/functional_smoke.py
```
