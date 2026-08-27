# Custom Metrics, Lightning, and DDP

## Purpose

Read this reference when you are implementing a custom `torchmetrics.Metric`, debugging metric states, using metrics inside `torch.nn.Module` or Lightning modules, or controlling distributed synchronization.

## Custom `Metric` implementation checklist

A custom module metric should usually implement exactly three methods/areas:

1. Class attributes, when known: `is_differentiable`, `higher_is_better`, and `full_state_update`.
2. `__init__(**kwargs)`: call `super().__init__(**kwargs)` and register every metric state with `self.add_state(...)`.
3. `update(...)` and `compute()`: update states in place, then compute from states.

Do not override `reset()` unless the normal state reset is genuinely wrong. The base class resets states registered through `add_state`, clears compute caches, and empties list states.

### Tensor-state template

```python
import torch
from torch import Tensor
from torchmetrics import Metric

class StreamingAccuracy(Metric):
    is_differentiable = False
    higher_is_better = True
    full_state_update = False  # batch states reduce independently

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_state("correct", default=torch.tensor(0), dist_reduce_fx="sum")
        self.add_state("total", default=torch.tensor(0), dist_reduce_fx="sum")

    def update(self, preds: Tensor, target: Tensor) -> None:
        preds = preds.argmax(dim=-1) if preds.ndim > target.ndim else preds
        if preds.shape != target.shape:
            raise ValueError("preds and target must have the same shape after class selection")
        self.correct += (preds == target).sum()
        self.total += target.numel()

    def compute(self) -> Tensor:
        return self.correct.float() / self.total.clamp_min(1)
```

Use tensor states for fixed-size sufficient statistics such as counts, sums, confusion-matrix bins, or running totals. Tensor states have constant memory with respect to the number of batches.

### List-state template

Use list states when `compute()` needs individual batch tensors rather than fixed-size totals. List states grow with the amount of data and must be reset after use.

```python
import torch
from torch import Tensor
from torchmetrics import Metric
from torchmetrics.utilities.data import dim_zero_cat

class MeanAbsoluteErrorFromList(Metric):
    is_differentiable = False
    higher_is_better = False
    full_state_update = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_state("errors", default=[], dist_reduce_fx="cat")

    def update(self, preds: Tensor, target: Tensor) -> None:
        if preds.shape != target.shape:
            raise ValueError("preds and target must have the same shape")
        self.errors.append((preds - target).detach().reshape(-1))

    def compute(self) -> Tensor:
        if isinstance(self.errors, list):
            if not self.errors:
                return torch.tensor(0.0, device=self.device)
            errors = dim_zero_cat(self.errors)
        else:
            errors = self.errors
        return errors.abs().mean()
```

For list states:

- `default` must be an empty list, not a pre-populated list.
- `dist_reduce_fx="cat"` is the usual distributed reducer for concatenating examples across ranks.
- Use `dim_zero_cat` in `compute()` so non-distributed lists and already-concatenated distributed tensors are handled consistently.
- Consider `compute_on_cpu=True` when GPU list states grow too large; it only applies to list states.
- Copy list-state values before `reset()` if you need to keep them elsewhere, because reset clears the list in place.

## `add_state` contract

`add_state(name, default, dist_reduce_fx=None, persistent=False)` accepts:

- `default`: a `torch.Tensor` or an empty `list`.
- `dist_reduce_fx`: one of `"sum"`, `"mean"`, `"cat"`, `"min"`, `"max"`, `None`, or a callable.
- `persistent`: whether this state appears in `state_dict()`.

The registered state becomes an attribute with the same name, appears in `metric.metric_state`, moves with `metric.to(device)`, and resets to the default on `metric.reset()`.

If `dist_reduce_fx=None`, synchronized tensor states are stacked across ranks and synchronized list states become a combined list without an automatic reduction. A custom callable receives the gathered state format, so write and test it with distributed shape/list behavior in mind.

## `full_state_update` and compute cache

`forward()` both accumulates global state and returns a batch result. The base class uses `full_state_update` to choose a safe or faster implementation:

- `full_state_update=True` or `None`: safe default for metrics whose update depends on existing global state; may call update logic more than once internally for a batch result.
- `full_state_update=False`: faster for metrics where each batch's state can be reduced independently into global state.

When creating a custom metric, compare results with `full_state_update=True` and `False` on multi-batch inputs. Only keep `False` if the batch result and accumulated result remain correct.

`compute()` caches results by default (`compute_with_cache=True`). Normal `update()` and `reset()` calls clear the cache. If your metric mutates state outside `update()` or returns mutable objects, disable caching with `compute_with_cache=False` or refactor so all state changes happen in `update()`.

## DDP synchronization controls

Module metrics synchronize state during `compute()` by default when distributed is initialized. The common controls are:

- `sync_on_compute=True`: default; `compute()` gathers and reduces states, then restores local unsynced state so accumulation can continue.
- `dist_sync_on_step=False`: default; avoid setting `True` unless step-level distributed values are required, because it synchronizes on every `forward()`.
- `process_group=...`: synchronize within a custom process group instead of all ranks.
- `dist_sync_fn=...`: customize the state-gather implementation.
- `metric.sync()`, `metric.unsync()`, and `metric.sync_context()`: advanced manual control; do not call `forward()` while a metric is already synced.

DDP caveats:

- If a Lightning method is restricted to rank zero and only rank zero updates/computes a metric, set `sync_on_compute=False`; otherwise other ranks can wait for a synchronization that never happens.
- Distributed samplers may pad uneven datasets by repeating samples so every process receives the same number of batches. For final test metrics where repeated samples would bias the result, evaluate on a single process or use a DDP join strategy that prevents padding bias.
- Functional metrics do not provide TorchMetrics' built-in distributed synchronization. If you use functional metrics in DDP, you own the reduction.

## PyTorch `nn.Module` registration pattern

Define metrics in `__init__`, not inside the training loop, and register them as child modules:

```python
import torch
from torch import nn
from torchmetrics import MetricCollection
from torchmetrics.classification import Accuracy

class ClassifierWithMetrics(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.net = nn.Linear(8, num_classes)
        self.acc = Accuracy(task="multiclass", num_classes=num_classes)
        self.extra_metrics = nn.ModuleDict({
            "val_acc": Accuracy(task="multiclass", num_classes=num_classes),
        })
        self.collection = MetricCollection({
            "acc": Accuracy(task="multiclass", num_classes=num_classes),
        })

    def forward(self, x):
        return self.net(x)
```

Avoid `self.metrics = [Accuracy(...)]` and `self.metrics = {"acc": Accuracy(...)}` because plain containers are invisible to PyTorch module traversal and device movement.

## Lightning logging patterns

Lightning adds three conveniences when metrics are registered on a `LightningModule`: automatic device placement, `self.log`/`self.log_dict` integration, and automatic reset when logging metric objects at epoch boundaries.

### Log a metric object

Use this when the metric returns a scalar tensor and you want Lightning to compute/reset at the right time.

```python
class LitClassifier(LightningModule):
    def __init__(self, num_classes: int):
        super().__init__()
        self.val_acc = Accuracy(task="multiclass", num_classes=num_classes)

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        self.val_acc.update(logits, y)
        self.log("val_acc", self.val_acc, on_step=False, on_epoch=True)
```

### Log computed values manually

Use this when you need custom names, non-standard epoch hooks, or outputs from a `MetricCollection`. Manual logging means you must reset manually.

```python
class LitClassifier(LightningModule):
    def __init__(self, num_classes: int):
        super().__init__()
        base = MetricCollection({
            "acc": Accuracy(task="multiclass", num_classes=num_classes),
        })
        self.train_metrics = base.clone(prefix="train_")
        self.val_metrics = base.clone(prefix="val_")

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        values = self.train_metrics(logits, y)
        self.log_dict(values, on_step=True, on_epoch=False)
        return self.loss(logits, y)

    def on_train_epoch_end(self):
        self.train_metrics.reset()

    def validation_step(self, batch, batch_idx):
        x, y = batch
        self.val_metrics.update(self(x), y)

    def on_validation_epoch_end(self):
        self.log_dict(self.val_metrics.compute(), on_step=False, on_epoch=True)
        self.val_metrics.reset()
```

Lightning rules:

- Do not mix object logging (`self.log("x", self.metric)`) with manual computed-value logging (`self.log("x", self.metric.compute())`) for the same metric stream.
- `self.log` and `self.log_dict` support scalar tensors. Metrics that return matrices, curves, lists, or nested dictionaries must be flattened, reduced to scalars, or handled outside Lightning scalar logging.
- When logging a `Metric` object, `sync_dist`, `sync_dist_group`, and `reduce_fx` on `self.log(...)` do not control TorchMetrics' own distributed synchronization. Configure the metric itself with `sync_on_compute`, `process_group`, or `dist_sync_fn`.
- Keep separate metric instances for train, validation, test, and each dataloader. For multiple dataloaders, use `nn.ModuleList` or `MetricCollection.clone(...)` so state does not mix.
