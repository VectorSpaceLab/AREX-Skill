# Trainer Workflows

This reference gives Composer `Trainer` recipes and API decision points for package-user workflows. Install with `pip install mosaicml` and import from `composer`.

## Core imports

```python
import torch
from torch.utils.data import DataLoader, TensorDataset

from composer import Trainer
from composer.core import DataSpec, Evaluator, Time, Timestamp
from composer.models import ComposerClassifier, ComposerModel
```

Use `from composer.core import Precision` only if code needs the enum; strings such as `"fp32"`, `"amp_fp16"`, and `"amp_bf16"` are accepted by `Trainer`.

## Minimal training recipe

```python
features = torch.randn(32, 8)
targets = torch.randint(0, 3, (32,))
train_loader = DataLoader(TensorDataset(features, targets), batch_size=8)
eval_loader = DataLoader(TensorDataset(features.clone(), targets.clone()), batch_size=8)

model = ComposerClassifier(torch.nn.Linear(8, 3), num_classes=3)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

trainer = Trainer(
    model=model,
    train_dataloader=train_loader,
    eval_dataloader=eval_loader,
    optimizers=optimizer,
    max_duration="4ba",
    device="cpu",
    precision="fp32",
    run_name="tiny-debug-run",
    progress_bar=False,
)
trainer.fit()
trainer.eval(subset_num_batches=1)
outputs = trainer.predict(eval_loader, subset_num_batches=1)
```

Expected checks after the run:

```python
assert int(trainer.state.timestamp.batch) == 4
assert trainer.state.train_metrics is not None
assert "eval" in trainer.state.eval_metrics
assert len(outputs) == 1
```

## Trainer construction decision points

| Decision | Use | Notes |
|---|---|---|
| `model` | Required `ComposerModel` | Use `ComposerClassifier` for ordinary classification, subclass `ComposerModel` otherwise. |
| `train_dataloader` | Iterable, `DataSpec`, or dict of `DataSpec` kwargs | Can also be supplied to `fit()` if omitted at init. |
| `max_duration` | `int`, `str`, or `Time` | Integers are epochs; strings include `"1ep"`, `"10ba"`, `"100sp"`, `"2048tok"`. |
| `optimizers` | One `torch.optim.Optimizer` | Composer can default when the model has parameters, but explicit is easier to debug. |
| `schedulers` | PyTorch LR scheduler, Composer scheduler, or sequence | Composer schedulers understand `Time` strings. |
| `eval_dataloader` | Loader, `DataSpec`, `Evaluator`, or sequence of `Evaluator` | Use `Evaluator` for labels, selected metric names, or per-loader intervals. |
| `callbacks` | Callback objects | Logging/profiling/artifact upload belongs in the observability sub-skill. |
| `algorithms` | Algorithm objects | Method choice and catalog belongs in the methods sub-skill. |
| `run_name` | Stable string | Needed for predictable checkpoint/log grouping and required for `autoresume=True`. |
| `device` | `None`, `"cpu"`, `"gpu"`, `"mps"`, `"tpu"`, or `Device` | `None` picks GPU if available, else CPU. |
| `precision` | `"fp32"`, `"amp_fp16"`, or `"amp_bf16"` | CPU requires `fp32`; GPU defaults to AMP FP16 when not specified. |

## Fitting patterns

### All required pieces at init

```python
trainer = Trainer(
    model=model,
    train_dataloader=train_loader,
    optimizers=optimizer,
    max_duration="2ep",
)
trainer.fit()
```

### Supply data and duration at `fit()`

```python
trainer = Trainer(model=model, optimizers=optimizer)
trainer.fit(train_dataloader=train_loader, duration="20ba")
```

This is useful for short debugging runs. If `train_dataloader` or duration is missing from both init and `fit()`, training raises a missing-argument error.

### Multiple calls to `fit()`

A later call must avoid ambiguous duration:

```python
trainer.fit()                     # uses initial max_duration
trainer.fit(duration="10ba")      # increments total max duration by 10 batches
trainer.fit(reset_time=True)       # resets timestamp and reuses the prior max duration
trainer.fit(reset_time=True, duration="1ep")
```

Use `reset_time=True` only when the new phase should behave like a fresh run for time-aware schedulers/algorithms. It does not reset model weights, gradients, optimizer state, or native PyTorch schedulers.

## Evaluation and prediction

### Standalone eval

```python
trainer = Trainer(model=model, train_dataloader=train_loader, optimizers=optimizer, max_duration="2ba")
trainer.fit()
trainer.eval(eval_dataloader=eval_loader, subset_num_batches=1)
print(trainer.state.eval_metrics["eval"])
```

If `eval_dataloader` was passed to `Trainer`, `trainer.eval()` can omit it. If no eval loader was ever configured, `eval()` raises `eval_dataloader must be provided`.

### Multiple eval datasets

```python
eval_a = Evaluator(label="validation", dataloader=val_loader, metric_names=["MulticlassAccuracy"])
eval_b = Evaluator(label="holdout", dataloader=holdout_loader, metric_names=["MulticlassAccuracy"])
trainer = Trainer(..., eval_dataloader=[eval_a, eval_b], eval_interval="1ep")
```

Do not mix raw loaders and `Evaluator` objects in the same `eval_dataloader` sequence. Wrap every loader with `Evaluator` when any one loader needs a label or selected metrics.

### Prediction

```python
predictions = trainer.predict(predict_loader, subset_num_batches=2, return_outputs=True)
assert isinstance(predictions, list)
```

`predict()` uses `model(batch)` and returns CPU copies of outputs when `return_outputs=True`. Use `return_outputs=False` only when a callback consumes outputs batch by batch; logger/artifact callbacks are routed to observability.

## Optimizers and schedulers

- Composer supports one optimizer in the standard Trainer path.
- If the model has parameters and no optimizer is supplied, Composer attempts a default optimizer and warns.
- If the model has no parameters, Composer cannot create an optimizer; `fit()` raises because training cannot step.
- Native PyTorch schedulers and Composer schedulers can be supplied through `schedulers`.
- Composer schedulers can use time strings such as `"0.5dur"` for milestones.
- `scale_schedule_ratio` and `step_schedulers_every_batch` only matter when schedulers are provided.

## Device and precision basics

- Start with `device="cpu", precision="fp32"` for logic validation.
- CPU plus `"amp_fp16"` or `"amp_bf16"` raises a precision validation error.
- `device="gpu"` requires CUDA availability; invalid strings such as `"magic_device"` raise `ValueError`.
- `device=None` auto-selects GPU when CUDA is available, otherwise CPU.
- TPU, MPS, multi-rank launch, FSDP, and auto-microbatching should be routed to distributed/backend-specific guidance.

## State observations to inspect

```python
state = trainer.state
print(state.run_name)
print(state.timestamp)          # Timestamp(...)
print(state.timestamp.batch)    # Time(..., TimeUnit.BATCH)
print(state.timestamp.sample)
print(state.timestamp.token)
print(state.train_metrics)
print(state.eval_metrics)
```

`State` centralizes model, optimizers, schedulers, callbacks, device, precision, dataloaders, metrics, and `Timestamp`. Check it before assuming the Trainer ignored an argument.

## Validation checklist

- One batch from the dataloader can be passed to `model.forward(batch)` and `model.loss(outputs, batch)`.
- `max_duration` uses a unit compatible with the dataloader: epoch durations require finite dataloader length or `train_subset_num_batches`.
- The optimizer sees the same model parameters that are passed to `Trainer`.
- CPU checks use `precision="fp32"`.
- `trainer.state.timestamp.batch`, `sample`, and `token` match the expected amount of work.
- `trainer.state.eval_metrics` is keyed by evaluator label, usually `"eval"` for a raw eval loader.
- Prediction output count equals the number of predict batches when `return_outputs=True`.
