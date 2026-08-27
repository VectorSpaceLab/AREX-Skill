# Model and Data Contracts

Composer training works when the model, dataloader, metrics, and `DataSpec` agree on a single batch schema. This reference focuses on `ComposerModel`, `ComposerClassifier`, `DataSpec`, `Evaluator`, eval, prediction, metrics, and custom batches.

## `ComposerModel` contract

Subclass `ComposerModel` when the batch is not ordinary `(inputs, targets)` classification or when evaluation/loss logic is custom.

Required methods:

```python
from typing import Any
import torch
import torch.nn.functional as F
from torchmetrics.classification import MulticlassAccuracy
from composer.models import ComposerModel

class MyModel(ComposerModel):
    def __init__(self, num_features: int, num_classes: int):
        super().__init__()
        self.net = torch.nn.Linear(num_features, num_classes)
        self.metric = MulticlassAccuracy(num_classes=num_classes)

    def forward(self, batch: tuple[torch.Tensor, torch.Tensor]) -> torch.Tensor:
        inputs, _ = batch
        return self.net(inputs)

    def loss(self, outputs: torch.Tensor, batch: tuple[torch.Tensor, torch.Tensor]) -> torch.Tensor:
        _, targets = batch
        return F.cross_entropy(outputs, targets)

    def get_metrics(self, is_train: bool) -> dict[str, Any]:
        return {"MulticlassAccuracy": MulticlassAccuracy(num_classes=2)}

    def update_metric(self, batch: Any, outputs: Any, metric: Any) -> None:
        _, targets = batch
        metric.update(outputs, targets)
```

Key rules:

- `forward(batch)` receives exactly the dataloader batch after `DataSpec` transforms and device movement.
- `loss(outputs, batch)` receives the output of `forward` and the same batch schema.
- `eval_forward(batch, outputs=None)` defaults to `outputs` when called during training eval or `forward(batch)` for standalone eval; override for self-supervised or generation-style validation.
- `get_metrics(is_train)` returns a mapping from metric name to TorchMetric. Composer deep-copies metrics for train/eval splits.
- `update_metric(batch, outputs, metric)` must match the metric's expected `update(...)` signature.

## `ComposerClassifier` contract

Use `ComposerClassifier(module, num_classes=None, train_metrics=None, val_metrics=None, loss_fn=soft_cross_entropy)` when:

- the dataloader yields `(inputs, targets)`;
- `module(inputs)` returns class logits;
- labels are compatible with the configured loss and metrics;
- default train/eval metrics are acceptable or custom metrics are supplied.

Example:

```python
module = torch.nn.Sequential(
    torch.nn.Linear(8, 16),
    torch.nn.ReLU(),
    torch.nn.Linear(16, 3),
)
model = ComposerClassifier(module=module, num_classes=3)
```

`num_classes` rules:

- If the wrapped `module` has a `num_classes` attribute, Composer uses it.
- If both module and argument provide `num_classes` but disagree, Composer warns and uses the module's value.
- If `num_classes` is unavailable and either train or validation metrics are omitted, construction raises and asks for `num_classes` or both metric sets.
- Wrong `num_classes` can produce metric errors or misleading accuracy even when the forward/loss path runs.

## Batch schemas

Common schemas that work without a custom `DataSpec`:

```python
# tuple classification
(inputs, targets)

# dictionary with tensors or lists
{"input_ids": tokens, "attention_mask": mask, "labels": labels}

# single tensor batch
inputs
```

The default sample counter expects tensors or tensor/list containers to have the same leading dimension. It raises when a dict contains unsupported values or when leading dimensions disagree.

For custom schemas, define the model and `DataSpec` together:

```python
def get_num_samples(batch: dict[str, torch.Tensor]) -> int:
    return batch["tokens"].shape[0]

def split_batch(batch: dict[str, torch.Tensor], microbatch_size: int):
    return [
        {name: value[start:start + microbatch_size] for name, value in batch.items()}
        for start in range(0, batch["tokens"].shape[0], microbatch_size)
    ]

train_spec = DataSpec(
    dataloader=train_loader,
    get_num_samples_in_batch=get_num_samples,
    split_batch=split_batch,
)
```

## `DataSpec` arguments

`DataSpec(dataloader, num_samples=None, num_tokens=None, batch_transforms=None, microbatch_transforms=None, split_batch=None, get_num_samples_in_batch=None, get_num_tokens_in_batch=None)` wraps an iterable or PyTorch `DataLoader`.

Use it for:

- `num_samples`: total samples per epoch when `len(dataloader.dataset)` is unavailable or wrong.
- `num_tokens`: total tokens per epoch for token-based progress estimates.
- `batch_transforms`: CPU-side transform applied before moving the batch to the device.
- `microbatch_transforms`: transform applied after device movement and after microbatching.
- `split_batch`: custom splitting for gradient accumulation when the default splitter cannot split your batch type.
- `get_num_samples_in_batch`: custom sample counts for ragged, nested, or non-tensor batches.
- `get_num_tokens_in_batch`: token counts used by `Timestamp.token` and token-based durations.

Do not iterate a `DataLoader` with persistent workers before passing it to `Trainer`; an active iterator triggers a validation error because Composer needs to inject dataset transforms safely.

## Token counting for text batches

Composer can track tokens through `Timestamp.token` when `DataSpec.get_num_tokens_in_batch` returns a count.

```python
PAD_ID = 0

def count_nonpad_tokens(batch: dict[str, torch.Tensor]) -> int:
    return int((batch["input_ids"] != PAD_ID).sum().item())

train_spec = DataSpec(
    dataloader=train_loader,
    get_num_tokens_in_batch=count_nonpad_tokens,
)

trainer = Trainer(
    model=model,
    train_dataloader=train_spec,
    optimizers=optimizer,
    max_duration="128tok",
)
trainer.fit()
assert int(trainer.state.timestamp.token) >= 128
```

For `accumulate_train_batch_on_tokens=True`, the token function may return a dictionary:

```python
def count_tokens(batch):
    nonpad = int((batch["input_ids"] != PAD_ID).sum().item())
    return {"total": nonpad, "loss_generating": nonpad // 2}
```

Composer uses `total` for time tracking and can use `loss_generating` for token-normalized loss accumulation.

## Evaluators

`Evaluator(label, dataloader, metric_names=None, subset_num_batches=None, eval_interval=None, device_eval_microbatch_size=None)` wraps an eval loader with metadata.

Use an `Evaluator` when:

- multiple validation datasets need distinct labels;
- one eval loader should compute only selected metrics;
- one eval loader needs a custom interval or subset size;
- evaluation batches need a `DataSpec`.

Example:

```python
from composer.core import Evaluator

val_eval = Evaluator(
    label="validation",
    dataloader=DataSpec(val_loader, get_num_tokens_in_batch=count_nonpad_tokens),
    metric_names=["MulticlassAccuracy"],
    subset_num_batches=10,
    eval_interval="1ep",
)
trainer = Trainer(..., eval_dataloader=[val_eval])
```

Metric names can be regex-like strings matched against keys returned by `model.get_metrics(False)`. If `metric_names` is omitted, all validation metrics are used.

## Eval and predict contracts

- `trainer.eval(eval_dataloader=..., subset_num_batches=...)` stores results in `trainer.state.eval_metrics[label][metric_name]`.
- `trainer.predict(dataloader, subset_num_batches=-1, return_outputs=True)` returns a list of batch outputs copied to CPU.
- Prediction uses the model forward path; it does not call `loss` or update metrics.
- If returned prediction outputs are too large, use `return_outputs=False` and consume `state.outputs` from a callback; route artifact/log upload details to observability.

## Custom batch validation steps

1. Print or assert the type and keys of one dataloader batch.
2. Run `outputs = model.forward(batch)` directly on CPU.
3. Run `loss = model.loss(outputs, batch)` and assert `loss.ndim == 0` or is otherwise backward-compatible.
4. Build `DataSpec` with explicit sample and token counters for non-trivial batches.
5. If using microbatching, call your `split_batch(batch, microbatch_size)` directly and verify every piece preserves schema.
6. Run `Trainer(..., max_duration="1ba", device="cpu", precision="fp32")`.
7. Check `trainer.state.timestamp.sample` and `trainer.state.timestamp.token` against expected values.
