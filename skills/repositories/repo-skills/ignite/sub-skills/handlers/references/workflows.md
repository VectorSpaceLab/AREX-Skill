# Handler workflows

## 1. Save the best checkpoint to disk

Use this pattern when you want to keep only the top-performing model state from validation.

```python
import tempfile
from pathlib import Path

import torch
from ignite.engine import Events, create_supervised_evaluator, create_supervised_trainer
from ignite.handlers import Checkpoint, DiskSaver
from ignite.metrics import Accuracy

model = torch.nn.Linear(4, 2)
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
loss_fn = torch.nn.CrossEntropyLoss()
trainer = create_supervised_trainer(model, optimizer, loss_fn)
evaluator = create_supervised_evaluator(model, metrics={"acc": Accuracy()})

with tempfile.TemporaryDirectory() as tmpdir:
    saver = DiskSaver(Path(tmpdir), create_dir=True, require_empty=False)
    checkpointer = Checkpoint(
        {"model": model, "optimizer": optimizer},
        saver,
        n_saved=1,
        filename_prefix="ignite",
        score_function=lambda engine: float(engine.state.metrics["acc"]),
        score_name="acc",
    )
    evaluator.add_event_handler(Events.COMPLETED, checkpointer)
```

Attach the evaluator to your validation step and let the handler retain the best file for you.

## 2. Stop early when validation stops improving

`EarlyStopping` belongs on the evaluator, not on the trainer. Pass the trainer into the handler so it can terminate the run.

```python
from ignite.engine import Events
from ignite.handlers import EarlyStopping

stopper = EarlyStopping(
    patience=3,
    score_function=lambda engine: float(engine.state.metrics["acc"]),
    trainer=trainer,
    threshold=0.0,
    mode="max",
)
evaluator.add_event_handler(Events.COMPLETED, stopper)
```

Use a validation metric that is already attached to the evaluator. If you need to minimize a score, set `mode="min"`.

## 3. Restore model and optimizer state

The checkpoint helper loads into arbitrary objects with `load_state_dict`.

```python
from ignite.handlers import Checkpoint

Checkpoint.load_objects(
    to_load={"model": model, "optimizer": optimizer},
    checkpoint="path/to/checkpoint.pt",
)
```

Use this when the goal is to resume training or inspect a saved model state, not to retain a file on disk.

## 4. Combine a warmup or cyclic schedule with the trainer

Parameter schedulers are ordinary event handlers. Attach them to iteration events when you want the learning rate to change every batch.

```python
from ignite.engine import Events
from ignite.handlers import LinearCyclicalScheduler, create_lr_scheduler_with_warmup

scheduler = LinearCyclicalScheduler(
    optimizer,
    param_name="lr",
    start_value=0.2,
    end_value=0.05,
    cycle_size=4,
)
trainer.add_event_handler(Events.ITERATION_STARTED, scheduler)
```

If the user asks for a staged warmup, use `create_lr_scheduler_with_warmup(...)` and keep the warmup duration aligned with the iteration count.

## 5. Add a progress bar and experiment logger

`ProgressBar` is the quickest way to expose metrics live. For structured logging, prefer `setup_tb_logging(...)` or one of the service-specific logger helpers.

```python
from ignite.handlers import ProgressBar
from ignite.handlers.logger_utils import setup_tb_logging

ProgressBar(persist=False).attach(trainer, metric_names="all")
tb_logger = setup_tb_logging(
    output_path="runs/tensorboard",
    trainer=trainer,
    optimizers=optimizer,
    evaluators={"validation": evaluator},
    log_every_iters=10,
)
```

Close the logger when training finishes.

## 6. Measure runtime and profiler overhead

Use `Timer` for a small timing probe and `BasicTimeProfiler` or `HandlersTimeProfiler` when you need more detailed timing breakdowns.

```python
from ignite.engine import Events
from ignite.handlers import BasicTimeProfiler, Timer

timer = Timer(average=True)
timer.attach(
    trainer,
    start=Events.STARTED,
    resume=Events.ITERATION_STARTED,
    pause=Events.ITERATION_COMPLETED,
    step=Events.ITERATION_COMPLETED,
)

profiler = BasicTimeProfiler()
profiler.attach(trainer)
```

`BasicTimeProfiler.write_results(...)` writes a CSV file and therefore needs `pandas`.

## 7. Handy shell of a complete handler workflow

A typical order is:

1. Build the trainer and evaluator.
2. Attach metrics to the evaluator.
3. Attach schedulers and timers to the trainer.
4. Attach checkpointing and early stopping to the evaluator completion event.
5. Attach a logger or progress bar to the trainer.

That sequence keeps the loop, the metrics, and the side effects separated cleanly.
