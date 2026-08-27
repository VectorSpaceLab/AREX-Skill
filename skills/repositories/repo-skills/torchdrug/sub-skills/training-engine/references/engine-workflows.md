# Engine Workflows

`torchdrug.core.Engine` is the high-level training and evaluation harness. It owns the task module, split datasets, optimizer, optional scheduler, device/distributed setup, logger/meter, checkpoint IO, and config serialization.

## Constructor Contract

```python
solver = core.Engine(
    task,
    train_set,
    valid_set,
    test_set,
    optimizer,
    scheduler=None,
    gpus=None,
    batch_size=1,
    gradient_interval=1,
    num_worker=0,
    logger="logging",
    log_interval=100,
)
```

- `task` is a `torch.nn.Module`, usually a `torchdrug.tasks.Task` plus `core.Configurable`, that returns `(loss, metric)` from `forward(batch)`.
- `train_set`, `valid_set`, and `test_set` are PyTorch/TorchDrug datasets or subsets. `evaluate(split)` looks up `train_set`, `valid_set`, or `test_set` by split name.
- `optimizer` is built from `task.parameters()`, not from the bare representation model, because task wrappers add prediction heads and buffers during preprocessing.
- `scheduler`, if provided, is stepped once at the end of every epoch in `train()`.
- `batch_size` is per process/device. With `gradient_interval=n`, each optimizer update accumulates up to `batch_size * n` samples per process.
- `num_worker` is passed to TorchDrug `data.DataLoader` per process/device.
- `log_interval` controls how often batch metrics are emitted after optimizer updates.

## Standard Training Skeleton

```python
import torch
from torchdrug import core, models, tasks

model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256, 256, 256],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,
)
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, batch_size=1024)
solver.train(num_epoch=100)
valid_metric = solver.evaluate("valid")
test_metric = solver.evaluate("test")
```

Use domain sub-skills for choosing `dataset`, task type, model family, split strategy, task labels, and metrics. This sub-skill only covers the Engine-facing mechanics.

## Fit / Evaluate / Predict

- `solver.train(num_epoch=1, batch_per_epoch=None)` iterates over `train_set`, sets `task.split = "train"`, calls `task(batch)`, backpropagates the returned loss, averages metrics across `gradient_interval`, and logs through the meter.
- `batch_per_epoch` limits each epoch to a random/sampled prefix of the distributed dataloader. Leave it unset for full-epoch training.
- `solver.evaluate("valid")` or `solver.evaluate("test")` sets `task.split` to the requested split, calls `task.predict_and_target(batch)`, concatenates predictions and targets, then calls `task.evaluate(pred, target)`.
- For ad hoc prediction, collate samples into the same batch shape the task expects and call `task.predict(batch)` directly. Move the batch to the same device as the Engine if using CUDA.

Example direct prediction:

```python
from torchdrug import data, utils

batch = data.graph_collate(valid_set[:8])
if solver.device.type == "cuda":
    batch = utils.cuda(batch, device=solver.device)
with torch.no_grad():
    pred = solver.model.predict(batch)
```

## Optimizer And Scheduler Wiring

Create the optimizer after constructing the task and before constructing the Engine:

```python
task = tasks.PropertyPrediction(model, task=dataset.tasks)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, scheduler=scheduler)
```

Task `preprocess()` may create new trainable modules after seeing the dataset, such as prediction heads. Engine records task parameters before and after preprocessing and automatically adds newly created parameters to the optimizer. This only works if the optimizer was created from the task parameters and passed into `Engine`.

## CPU, GPU, And Distributed Settings

- CPU-only: pass `gpus=None` or omit `gpus`. This is the safest smoke-test and CI mode.
- Single GPU: pass `gpus=[0]` and run a normal Python process.
- Single-node multi-GPU: launch one process per GPU with distributed launch and pass one GPU id per process, such as `gpus=[0, 1, 2, 3]`.
- Multi-node distributed GPU: repeat the node-local GPU ids for each node in process-rank order, such as `gpus=[0, 1, 2, 3, 0, 1, 2, 3]` for two four-GPU nodes.
- Distributed CPU: launch multiple processes with `gpus=None`; Engine uses the `gloo` backend.

Engine checks `len(gpus) == world_size` when `gpus` is not `None`. If `world_size == 1`, `gpus=[0, 1]` is invalid unless the script was launched as two distributed processes.

The distributed launch style in TorchDrug 0.2.1 documentation is:

```bash
python -m torch.distributed.launch --nproc_per_node=4 train.py
```

For newer PyTorch installations, `torchrun --nproc_per_node=4 train.py` is the modern equivalent, but verify compatibility with the installed PyTorch version.

## Logging

- `logger="logging"` uses Python logging and is dependency-free.
- `logger="wandb"` constructs `core.WandbLogger(project=task.__class__.__name__)`; it requires the `wandb` package and configured credentials or offline mode.
- A custom logger can be passed as an instance implementing `core.LoggerBase.log(record, step_id, category)` and `log_config(config)`.
- Engine logs `solver.config_dict()` during construction, so config serialization failures can appear before training starts.

## Checkpoint Save / Load

`solver.save(checkpoint)` writes a PyTorch checkpoint containing two keys:

- `model`: `solver.model.state_dict()`
- `optimizer`: `solver.optimizer.state_dict()`

`solver.load(checkpoint, load_optimizer=True, strict=True)` loads model weights and, by default, optimizer state. Use these patterns:

```python
solver.save("model_epoch_100.pth")
solver.load("model_epoch_100.pth")
solver.load("model_epoch_100.pth", load_optimizer=False)       # inference or fine-tuning
solver.load("model_epoch_100.pth", strict=False)              # changed head / partial migration
```

Use `strict=False` only when you intentionally changed model/task structure and have reviewed missing or unexpected parameters. If optimizer structure changed, also pass `load_optimizer=False`.

## Config Serialization

TorchDrug separates hyperparameters from weights:

```python
import json
from torchdrug import core

with open("experiment.json", "w") as fout:
    json.dump(solver.config_dict(), fout)
solver.save("experiment.pth")

with open("experiment.json") as fin:
    solver = core.Configurable.load_config_dict(json.load(fin))
solver.load("experiment.pth", load_optimizer=False)
```

Important details:

- Classes must be registered with `torchdrug.core.Registry` to round-trip through `core.Configurable.load_config_dict()` from a generic config.
- Engine has a custom `load_config_dict`: it reconstructs nested configurable objects, then rebuilds the optimizer with `params=new_task.parameters()`.
- Configs capture constructor arguments, including dataset split objects if they are passed into the Engine. For portable experiment metadata, store dataset construction/split code separately from the Engine config when dataset objects are not JSON-serializable.
- Checkpoint files contain weights and optimizer state; JSON config files contain hyperparameters and object graph. Use both to fully recreate a solver.

## Safe Smoke Patterns

For quick validation without downloads or training:

- Check model/task constructors with small dimensions.
- Call `config_dict()` and `core.Configurable.load_config_dict()` on registered configurable models.
- Avoid dataset constructors that download files.
- Keep Engine smoke tests CPU-only unless the user explicitly asks for GPU validation.
- Use the bundled `scripts/smoke_config_roundtrip.py` as a minimal no-data serialization check.
