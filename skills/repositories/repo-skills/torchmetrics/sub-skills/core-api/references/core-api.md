# TorchMetrics Core API Reference

## Purpose

Read this reference when you need to use the common TorchMetrics API correctly before choosing a specific metric family. It focuses on installation/import sanity, functional versus module metrics, metric lifecycle, device and dtype placement, `MetricCollection`, and persistent metric state.

## Minimal install and import sanity

TorchMetrics is a Python package used from Python imports; the verified package has no console entry point. A minimal runtime needs `torch` and `torchmetrics`; many specialized metric families also need optional extras, but the core API examples below require no downloads. The installed package re-exports common core objects from `torchmetrics` itself, including `Metric`, `MetricCollection`, `Accuracy`, `MeanSquaredError`, and `functional`.

```bash
pip install torchmetrics
python -c "import torch, torchmetrics; from torchmetrics.classification import Accuracy; Accuracy(task='multiclass', num_classes=3); print(torchmetrics.__version__)"
```

For a stronger bundled smoke check, run:

```bash
python scripts/core_metric_smoke.py --device auto
```

Expected observations: the script prints a JSON summary with numeric values for accuracy, MSE, a metric collection, and a custom metric. If `--device cuda` is requested without CUDA, the script exits with a clear error instead of silently falling back.

## Functional versus module metrics

| Need | Use functional metric | Use module `Metric` |
|---|---:|---:|
| One independent batch or small in-memory tensor set | yes | optional |
| No internal state after the call | yes | no |
| Accumulate many batches before final `compute()` | no | yes |
| Built-in DDP state synchronization | no | yes |
| PyTorch Lightning object logging and auto-reset | no | yes |
| `MetricCollection`, arithmetic/composition, or persistent state | no | yes |
| Lowest memory for one-shot calculations | usually | no |

Functional metrics are plain functions that take tensors and return tensors, for example:

```python
import torch
from torchmetrics.functional import accuracy

preds = torch.tensor([[0.1, 0.8, 0.1], [0.7, 0.2, 0.1]])
target = torch.tensor([1, 2])
batch_acc = accuracy(preds, target, task="multiclass", num_classes=3)
```

Module metrics are `torch.nn.Module` subclasses with state:

```python
import torch
from torchmetrics.classification import Accuracy

metric = Accuracy(task="multiclass", num_classes=3)
for logits, target in batches:
    batch_value = metric(logits, target)  # updates global state and returns this batch's metric value

epoch_value = metric.compute()            # accumulated metric over all updates/forwards
metric.reset()                            # ready for the next independent epoch/stage
```

## Lifecycle: `update`, `compute`, `forward`, and `reset`

All module metrics share the same lifecycle contract:

| Method | What it does | Return value | Common use |
|---|---|---|---|
| `metric.update(*args, **kwargs)` | Mutates metric states in place. | `None` | Efficient accumulation when you only need epoch-level output. |
| `metric.compute()` | Computes from accumulated state; synchronizes distributed state by default. | Tensor, dict, list, or nested structure depending on the metric. | End-of-epoch/evaluation result. |
| `metric(*args, **kwargs)` or `metric.forward(...)` | Updates accumulated state and also computes the value for the current batch. | Same form as `compute()`, but for the current batch. | Step-level logging or quick checks while still accumulating. |
| `metric.reset()` | Restores all `add_state` states to their defaults and clears cached computed values. | `None` | Boundary between epochs, stages, dataloaders, or independent evaluations. |

Important semantics:

- The value returned by `metric(...)` is the current batch result, not the final accumulated result. The global state is still updated.
- `compute()` returns the accumulated result from all previous `update()` and `forward()` calls since the last `reset()`.
- `compute()` caches its result when `compute_with_cache=True` (the default). A later `update()` or `reset()` clears the cache.
- Calling `compute()` before any `update()` or `forward()` may warn because no user data has been accumulated.
- `reset()` clears tensor states back to cloned defaults and empties list states; call it before reusing a metric for a different logical stream.

A concrete accumulated-versus-batch pattern:

```python
from torchmetrics.classification import Accuracy

acc = Accuracy(task="multiclass", num_classes=3)

batch0 = acc(logits0, target0)  # result for batch0, state includes batch0
acc.update(logits1, target1)    # state now includes batch0 and batch1, no return
all_seen = acc.compute()        # result for batch0 + batch1
acc.reset()
```

## Constructor kwargs shared by module metrics

Metric classes accept their metric-specific arguments plus base `Metric` keyword arguments through `**kwargs`:

| Base kwarg | Use |
|---|---|
| `compute_on_cpu` | Move list states to CPU after updates to reduce accelerator memory pressure; applies to list states only. |
| `dist_sync_on_step` | Synchronize state during `forward()`; usually avoid because per-step synchronization is expensive. |
| `process_group` | Limit distributed synchronization to a specific process group. |
| `dist_sync_fn` | Override the function used to gather distributed state. |
| `distributed_available_fn` | Override the check that decides whether distributed synchronization is active. |
| `sync_on_compute` | Synchronize state when `compute()` is called; default is `True`. |
| `compute_with_cache` | Cache repeated `compute()` calls until the next update/reset; default is `True`. |

Unexpected keyword names are rejected by the base class. When debugging, first separate metric-specific arguments from base `Metric` kwargs and check spelling.

## Device and dtype placement

Metric states behave like module buffers for device moves, but they are not ordinary `nn.Module` buffers for persistence by default.

Recommended placement pattern:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
metric = Accuracy(task="multiclass", num_classes=3).to(device)
logits = logits.to(device)
target = target.to(device)
value = metric(logits, target)
```

Inside an `nn.Module` or Lightning module, define metrics in `__init__` as child modules. Then `model.to(device)` moves metric states along with the model. Valid containers are direct attributes, `torch.nn.ModuleList`, `torch.nn.ModuleDict`, and `MetricCollection`; plain `list` and `dict` do not register children.

Metric dtype conversion is intentionally guarded. Use `metric.set_dtype(torch.float64)` when you need metric states in a different dtype; do not rely on `metric.half()`, `metric.float()`, `metric.double()`, or `module.half()` to convert metric states.

You can inspect placement with:

```python
print(metric.device)
print(metric.dtype)
print(metric.metric_state)
```

## `MetricCollection` basics

Use `MetricCollection` when multiple metrics share the same input signature and should be updated/computed together.

```python
from torchmetrics import MetricCollection
from torchmetrics.classification import MulticlassAccuracy, MulticlassPrecision, MulticlassRecall

base = MetricCollection(
    {
        "acc": MulticlassAccuracy(num_classes=3),
        "precision": MulticlassPrecision(num_classes=3, average="macro"),
        "recall": MulticlassRecall(num_classes=3, average="macro"),
    }
)
train_metrics = base.clone(prefix="train_")
val_metrics = base.clone(prefix="val_")

step_values = train_metrics(preds, target)  # dict with train_* keys
val_metrics.update(preds, target)
epoch_values = val_metrics.compute()
val_metrics.reset()
```

Rules of thumb:

- Use a `dict` when names matter or when you need multiple instances of the same class with different parameters.
- A list/tuple uses metric class names as output keys; duplicate class names in a list are invalid.
- `prefix` and `postfix` rename output keys and are useful for train/validation/test separation.
- `MetricCollection` forwards positional arguments to every metric and filters keyword arguments per metric update signature.
- Compute groups can reduce repeated work for compatible metrics when using `update()`; that optimization does not apply in the same way to `forward()`.

## Persistent metric state and `state_dict`

By default, metric states are not added to `state_dict()`. This preserves compatibility with models that did not previously include metric state. Enable persistence only when the accumulated metric state is intentionally part of a checkpoint or handoff.

```python
import torch
from torchmetrics.classification import MulticlassAccuracy

metric = MulticlassAccuracy(num_classes=5)
metric.persistent(True)
metric.update(preds, target)
torch.save(metric.state_dict(), "metric_state.pt")

restored = MulticlassAccuracy(num_classes=5)
restored.load_state_dict(torch.load("metric_state.pt", map_location="cpu"))
```

For custom metrics, you can also set `persistent=True` on selected `add_state` calls. Use `map_location` when loading state saved from another device.
