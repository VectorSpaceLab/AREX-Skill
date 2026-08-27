# Engine workflows

## 1. Build a supervised trainer and evaluator

Use this pattern when you want Ignite to manage the training loop but keep your model, optimizer, and loss function explicit.

```python
import torch
from ignite.engine import create_supervised_trainer, create_supervised_evaluator
from ignite.metrics import Accuracy

model = torch.nn.Linear(4, 2)
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
loss_fn = torch.nn.CrossEntropyLoss()

trainer = create_supervised_trainer(model, optimizer, loss_fn, device="cpu")
evaluator = create_supervised_evaluator(model, metrics={"acc": Accuracy()})
```

Attach metrics to the evaluator and call `trainer.run(train_loader, max_epochs=...)`. The evaluator returns a `state.metrics` mapping.

## 2. Resume a run from engine state

The engine keeps its own state object. Save and restore that state when you need a restartable loop.

```python
state = trainer.state_dict()
# ... create a fresh trainer or reuse the same one ...
trainer.load_state_dict(state)
trainer.run(train_loader, max_epochs=target_epochs)
```

This route is the right place for `state_dict` / `load_state_dict` questions. If the task also needs checkpoint files on disk, switch to the handlers sub-skill for `Checkpoint` and `DiskSaver`.

## 3. Use deterministic dataflow

When reproducibility matters, combine `DeterministicEngine` or `deterministic=True` with a fixed seed and a loader that can be replayed.

- Seed Python, NumPy, and PyTorch with `ignite.utils.manual_seed(seed)`.
- Keep the same `epoch_length` while resuming.
- Do not introduce handlers that reseed the RNG in the middle of the epoch unless you know the effect on reproducibility.

## 4. Customize batch and model flow

Use the helper hooks when your batch or model outputs are not already in `(x, y)` / `(y_pred, y)` form.

- `prepare_batch` moves or restructures a batch.
- `model_transform` adjusts the model output before loss or metrics.
- `output_transform` defines what the engine stores in `state.output`.
- `model_fn` lets you swap out the exact model invocation.

These hooks are the normal place to adapt sequence models, multi-output models, or custom preprocessing pipelines.

## 5. Gradient accumulation and AMP

- Set `gradient_accumulation_steps` above `1` when you want the trainer to step the optimizer less frequently.
- Use `amp_mode="amp"` for native AMP, `amp_mode="apex"` only if Apex is installed, and an XLA device for TPU helpers.
- Keep `scaler` aligned with `amp_mode="amp"`; the helper validates the combination.

## 6. Common example families

These example families are the fastest way to recognize the engine route:

- MNIST save/resume and crash-recovery examples.
- Super-resolution training and inference examples.
- Reinforcement-learning trainer functions that use custom process functions.
- Siamese-network or other non-classification examples that still rely on Ignite's engine loop.

## 7. What to hand off to other routes

- Checkpoint file naming, retention, and restore helpers -> handlers.
- Metric definitions and math -> metrics.
- Backend launchers, `torchrun`, or Horovod/XLA setup -> distributed.

## Good difficult cases

- Resume a partially completed supervised run and confirm the loaded trainer continues from the next epoch rather than starting over.
- Switch the same loop between deterministic and non-deterministic modes and verify the generated outputs change only when the seed/dataflow changes.
