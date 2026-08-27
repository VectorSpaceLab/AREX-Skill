# Engine API reference

## Core classes and functions

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `Engine(process_function)` | Runs a user-defined step function over an iterable or fixed-length stream. | The process function receives `(engine, batch)` and may update `engine.state`. |
| `Events` / `EventEnum` / `EventsList` / `CallableEventWithFilter` | Event vocabulary and filters for attaching callbacks. | Use `Events.EPOCH_COMPLETED(every=5)` and similar filters for periodic hooks. |
| `State` | Mutable run state carried by the engine. | Common fields: `epoch`, `iteration`, `epoch_length`, `max_epochs`, `max_iters`, `output`, `metrics`, `times`, `dataloader`. |
| `DeterministicEngine` | Engine variant that helps with reproducible dataflow. | Pair with `manual_seed` and reproducible loaders when you need restartable runs. |
| `create_supervised_trainer(...)` | Builds a trainer update function and wraps it in `Engine` or `DeterministicEngine`. | Handles `device`, `prepare_batch`, `model_transform`, `output_transform`, `amp_mode`, `scaler`, `gradient_accumulation_steps`, and `model_fn`. |
| `create_supervised_evaluator(...)` | Builds a supervised inference engine and optionally attaches metrics. | Returns an `Engine` whose default output is `(y_pred, y)`. |
| `supervised_training_step*` / `supervised_evaluation_step*` | Lower-level factories for custom training/eval steps. | Variants exist for plain, AMP, Apex, and TPU/XLA execution. |
| `ReproducibleBatchSampler` / `keep_random_state` / `update_dataloader` | Utilities for repeatable dataflow. | Useful when you need deterministic batch order after a resume. |

## `Engine.run(...)`

`run(data=None, max_epochs=None, max_iters=None, epoch_length=None)` is the central entry point.

- `data` must be iterable when provided.
- `max_epochs` and `max_iters` are mutually exclusive.
- `epoch_length` is required when `data` is `None`.
- When resuming, keep `epoch_length` consistent with the saved state.

## Trainer and evaluator customization

- `prepare_batch(batch, device, non_blocking)` moves batch tensors to the chosen device.
- `model_transform(output)` reshapes a model output into the form expected by the loss or metric.
- `output_transform(x, y, y_pred, loss)` or `output_transform(x, y, y_pred)` defines what the engine stores in `state.output`.
- `model_fn(model, x)` lets you override the model call itself.
- `deterministic=True` switches `create_supervised_trainer` to `DeterministicEngine`.
- `amp_mode` can be `"amp"`, `"apex"`, or `None`; TPU/XLA is chosen by passing an XLA device string.

## Event patterns worth remembering

- `engine.add_event_handler(event_name, handler, *args, **kwargs)` attaches a callback.
- `@engine.on(...)` is a shorthand decorator for the same operation.
- Typical events: `STARTED`, `EPOCH_STARTED`, `ITERATION_STARTED`, `ITERATION_COMPLETED`, `EPOCH_COMPLETED`, `COMPLETED`.
- Custom events are useful for backprop, optimizer, or sequence-model phases.

## What to read next

Use `references/workflows.md` for end-to-end trainer/evaluator recipes and `references/troubleshooting.md` for resume, AMP, deterministic, and epoch-length failures.
