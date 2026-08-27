# Plotting and Tracking Workflows

## 1) Train/validation collections with prefixes

```python
from torchmetrics import MetricCollection
from torchmetrics.classification import MulticlassAccuracy, MulticlassF1Score

base = MetricCollection({
    "acc": MulticlassAccuracy(num_classes=3),
    "f1": MulticlassF1Score(num_classes=3, average="macro"),
})
train_metrics = base.clone(prefix="train_")
val_metrics = base.clone(prefix="val_")

train_step_values = train_metrics(preds, target)
val_metrics.update(preds, target)
val_epoch_values = val_metrics.compute()
val_metrics.reset()
```

Practical notes:

- Use independent clones for train/validation/test streams.
- In Lightning, scalar dict values can be passed to `self.log_dict`; non-scalar values need flattening or manual handling.

## 2) Classwise outputs

```python
from torchmetrics.classification import MulticlassAccuracy
from torchmetrics.wrappers import ClasswiseWrapper

metric = ClasswiseWrapper(
    MulticlassAccuracy(num_classes=3, average=None),
    labels=["cat", "dog", "horse"],
    prefix="val_acc_",
)
print(metric(preds, target))
```

Practical notes:

- The wrapped metric must return one value per class.
- Labels should match the class order used by the model and targets.

## 3) Track best values over epochs

```python
from torchmetrics.classification import MulticlassAccuracy
from torchmetrics.wrappers import MetricTracker

tracker = MetricTracker(MulticlassAccuracy(num_classes=3), maximize=True)
for epoch in range(3):
    tracker.increment()
    for preds, target in epoch_batches[epoch]:
        tracker.update(preds, target)
    print(tracker.compute())

best_value, best_step = tracker.best_metric(return_step=True)
all_values = tracker.compute_all()
```

Practical notes:

- Call `increment()` before updating a new step/epoch.
- Provide `maximize=` explicitly when the wrapped metric does not expose `higher_is_better`.

## 4) Bootstrap uncertainty

```python
from torchmetrics.classification import BinaryAccuracy
from torchmetrics.wrappers import BootStrapper

metric = BootStrapper(BinaryAccuracy(), num_bootstraps=20, mean=True, std=True, quantile=0.95)
print(metric(preds, target))
```

Practical notes:

- Bootstrap outputs are dict-like and may need flattening before logging.
- Use a deterministic seed in experiments when comparing bootstrap behavior.

## 5) Headless plotting

```python
import matplotlib
matplotlib.use("Agg")

from torchmetrics.classification import BinaryAccuracy

metric = BinaryAccuracy()
metric.update(preds, target)
fig, ax = metric.plot()
fig.savefig("metric.png")
```

Practical notes:

- `.plot()` returns `(fig, ax)` for most metrics.
- You can pass `val=` to plot precomputed values or a list of values.
- You can pass `ax=` to draw into an existing subplot.
- `MetricCollection.plot(together=True)` tries to combine scalar metrics in one plot.

## 6) Smoke script workflow

```bash
python scripts/collections_wrappers_smoke.py
python scripts/collections_wrappers_smoke.py --plot ./torchmetrics-plot.png
```

The helper uses an Agg backend and deterministic tiny tensors.
