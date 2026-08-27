# Training and evaluation recipe

This workflow covers the standard path for Snorkel discriminative classification:

1. build tensor-backed datasets,
2. define a task graph,
3. train with `Trainer`,
4. score predictions,
5. add logging, checkpointing, and probabilistic-label support.

## 1) Create tensors and datasets

Use `torch.Tensor` inputs and keep label tensors explicit:

- hard labels: `torch.long` vectors with class ids
- probabilistic labels: `float` matrices with one row per example and one column per class

```python
import torch
from snorkel.classification import DictDataset, DictDataLoader

X_train = torch.tensor([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
Y_train = torch.tensor([[0.9, 0.1], [0.8, 0.2], [0.2, 0.8], [0.1, 0.9]])

X_valid = torch.tensor([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
Y_valid = torch.tensor([0, 0, 1, 1])

train_ds = DictDataset.from_tensors(
    X_train,
    Y_train,
    split="train",
    task_name="demo_task",
    dataset_name="DemoSet",
)
valid_ds = DictDataset.from_tensors(
    X_valid,
    Y_valid,
    split="valid",
    task_name="demo_task",
    dataset_name="DemoSet",
)

train_dl = DictDataLoader(train_ds, batch_size=2, shuffle=False)
valid_dl = DictDataLoader(valid_ds, batch_size=2, shuffle=False)
```

## 2) Define the task graph

A task is a sequence of named operations over a module pool.

```python
import torch.nn as nn
from snorkel.analysis import Scorer
from snorkel.classification import MultitaskClassifier, Operation, Task, cross_entropy_with_probs

module_pool = nn.ModuleDict(
    {
        "hidden": nn.Sequential(nn.Linear(2, 4), nn.ReLU()),
        "head": nn.Linear(4, 2),
    }
)

op_sequence = [
    Operation(module_name="hidden", inputs=[("_input_", "input_data")], name="hidden"),
    Operation(module_name="head", inputs=["hidden"], name="logits"),
]

task = Task(
    name="demo_task",
    module_pool=module_pool,
    op_sequence=op_sequence,
    scorer=Scorer(metrics=["accuracy"]),
    loss_func=cross_entropy_with_probs,
)

model = MultitaskClassifier([task], device=-1, dataparallel=False)
```

Notes:
- Use `"_input_"` to refer to the raw model input dictionary.
- Use `(op_name, field_key)` only when an upstream module returns a dictionary.
- Reuse module names across tasks when you want shared parameters.

## 3) Train with `Trainer`

`Trainer` handles batching, loss accumulation, logging, evaluation, and checkpointing.

```python
from snorkel.classification import Trainer

trainer = Trainer(
    n_epochs=1,
    progress_bar=False,
    batch_scheduler="sequential",
    logging=True,
    log_writer="json",
    log_writer_config={"log_dir": "./logs", "run_name": "demo_run"},
    checkpointing=True,
    checkpointer_config={
        "checkpoint_dir": "./checkpoints",
        "checkpoint_metric": "demo_task/DemoSet/valid/accuracy:max",
    },
)

trainer.fit(model, [train_dl, valid_dl])
```

What happens during training:
- batches are drawn from the training loaders in the configured order,
- logits are converted to losses per task,
- the validation split is scored at the configured evaluation frequency,
- logs and best checkpoints are written when the trigger conditions are met.

## 4) Evaluate predictions

`score()` returns metric keys that include the task, dataset, split, and metric name.

```python
scores = model.score([valid_dl])
# Example key:
# "demo_task/DemoSet/valid/accuracy"

predictions = model.predict(valid_dl, return_preds=True)
# predictions contains golds, probs, and preds by label name
```

Use `as_dataframe=True` when you want a tabular result for reporting:

```python
scores_df = model.score([valid_dl], as_dataframe=True)
```

## 5) Use probabilistic labels intentionally

When training with soft labels:

- keep the target tensor shaped `[n_examples, n_classes]`
- use `cross_entropy_with_probs`
- keep your evaluation split on hard labels if you want standard classification metrics

If you already have hard predictions and need soft targets, convert them with `preds_to_probs` from the utility module.

## 6) Log and checkpoint cleanly

- `LogWriter` writes scalar histories to JSON-style files.
- `TensorBoardWriter` writes the same metrics to TensorBoard.
- `Checkpointer` expects metric keys of the form `task/dataset/split/metric:mode` in its configuration.
- `LogManager` decides when to evaluate and when to checkpoint.

Typical metric key examples:
- `demo_task/DemoSet/valid/accuracy`
- `demo_task/DemoSet/train/loss`
- `model/all/train/loss`

## 7) Inspect score outputs and errors

For deeper inspection:

- use `Scorer.score()` for a metric bundle on a single gold/pred/prob set,
- use `Scorer.score_slices()` when you have a slice recarray,
- use `get_label_buckets()` and `get_label_instances()` to inspect buckets of errors or successes,
- use `metric_score()` when you want a direct metric call without creating a `Scorer`.

## Minimal checklist

- Dataset labels are `torch.Tensor` objects.
- The train split exists.
- Operation names are unique within the graph.
- The checkpoint metric string matches the metric key namespace.
- The chosen optimizer, lr scheduler, log writer, and batch scheduler are supported names.
- Probabilistic targets have one row per example and sum to 1 across classes.