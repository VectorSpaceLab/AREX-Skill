# Training Engine Troubleshooting

Use this guide when Engine construction, training, evaluation, logging, config loading, or checkpoint loading fails.

## Dataset Split And Batch Shape Issues

Symptoms:

- `evaluate("valid")` fails because `valid_set` is `None`.
- `KeyError: 'graph'` or missing task label keys.
- Collation fails for ad hoc prediction.
- Property prediction metrics are `nan` or labels are ignored.

Checks and fixes:

- `solver.evaluate(split)` expects the corresponding `solver.train_set`, `solver.valid_set`, or `solver.test_set` to be a real dataset. Do not evaluate a split that was passed as `None`.
- For graph/molecule property tasks, each sample should include `"graph"` and the task label names configured in `tasks.PropertyPrediction(..., task=...)`.
- For semi-supervised property prediction, unlabeled samples may set `"labeled"` false; otherwise labels should be numeric and non-`nan` for metrics to be meaningful.
- Use TorchDrug collation helpers such as `data.graph_collate(samples)` for direct graph prediction instead of raw Python lists.
- If `torch.utils.data.random_split()` creates lengths manually, ensure the lengths sum exactly to `len(dataset)`.

## Missing Optimizer Parameters

Symptoms:

- Newly created task heads do not train.
- Loss does not improve although the representation model is called.
- `RuntimeError: Loss doesn't require grad. Did you define any loss in the task?`

Checks and fixes:

- Build the optimizer from `task.parameters()`, not `model.parameters()`.
- Construct the optimizer before Engine construction and pass it into Engine. Engine compares parameters before and after `task.preprocess()` and appends newly created parameters to the optimizer.
- Ensure custom `forward()` adds a differentiable criterion to `all_loss` and returns `(all_loss, metric)`.
- If all parameters are frozen intentionally, do not expect Engine training to work without a differentiable trainable loss.
- If a custom task creates modules outside `preprocess()` or `__init__()`, verify those parameters are present in the optimizer.

## Device And `gpus` Errors

Symptoms:

- `ValueError: World size is 1 but found 2 GPUs... Did you launch with python -m torch.distributed.launch?`
- CUDA tensors and CPU tensors are mixed.
- Apple Silicon users try `mps` and TorchDrug does not use it.
- Distributed initialization hangs or fails.

Checks and fixes:

- Use CPU mode with `gpus=None` or omit `gpus`; do not pass `gpus=[]`.
- For one normal Python process on one GPU, use `gpus=[0]`.
- For multiple GPU ids, launch one process per id with distributed launch; `len(gpus)` must equal distributed `world_size`.
- Engine moves batches to CUDA inside `train()` and `evaluate()`, but direct calls to `task.predict(batch)` must move the batch first, for example with `utils.cuda(batch, device=solver.device)`.
- TorchDrug 0.2.1 documentation notes Apple Silicon support is CPU-only and does not support `mps` devices.
- For distributed CPU, omit `gpus` so Engine chooses the `gloo` backend. For distributed CUDA, Engine chooses `nccl`.

## W&B Logger Failures

Symptoms:

- `ModuleNotFoundError: Wandb is not found. Please install it with pip install wandb`.
- W&B prompts for login or cannot write run metadata.
- Multiple runs unexpectedly share the same W&B run.

Checks and fixes:

- Use `logger="logging"` for dependency-free scripts, smoke tests, and CI.
- Install and configure `wandb` before using `logger="wandb"`.
- Configure credentials or W&B offline mode outside TorchDrug if running on a headless or restricted machine.
- If a W&B run is already active, TorchDrug reuses it and warns. Call `wandb.finish()` before creating another run if reuse is not desired.
- A custom logger must implement both `log(record, step_id, category)` and `log_config(config)`.

## Configurable Registration And Load Failures

Symptoms:

- `KeyError: Can't find any registered key containing ...`.
- `KeyError: Ambiguous key ...`.
- `ValueError: Expect config class to be ...`.
- JSON dumping `solver.config_dict()` fails on non-serializable objects.

Checks and fixes:

- Import the module that defines a custom `@R.register(...)` class before calling `core.Configurable.load_config_dict(config)`.
- Register custom classes with stable, unique keys such as `models.MyModel` or `tasks.MyTask`.
- Inherit `core.Configurable` in the exact class whose constructor arguments need to be captured.
- Use the class-specific `load_config_dict()` only when the config `"class"` matches that class. Use `core.Configurable.load_config_dict()` for generic configs.
- Avoid putting live file handles, lambdas, transforms, raw datasets, or other non-JSON objects into constructors if the config must be saved as JSON.
- Engine configs include `train_set`, `valid_set`, `test_set`, optimizer, and scheduler constructor arguments. For portable experiment recipes, separately store the dataset construction and split code if those objects are not JSON-serializable.

## Checkpoint Strict Mismatch

Symptoms:

- Missing or unexpected keys from `load_state_dict`.
- Optimizer state load fails after changing task heads, model dimensions, or parameter groups.
- Loading on CPU/GPU fails because optimizer state tensors are on the wrong device.

Checks and fixes:

- Recreate the same task/model structure from the same config before loading weights when exact restoration is intended.
- Use `solver.load(path, load_optimizer=False)` for inference, transfer learning, changed optimizers, or changed parameter groups.
- Use `solver.load(path, strict=False, load_optimizer=False)` only for intentional partial migration, such as replacing a prediction head.
- If dimensions changed, inspect the affected module names and decide whether to drop, reinitialize, or remap those weights.
- Engine loads checkpoints with `map_location=solver.device` and moves optimizer state tensors to that device when optimizer loading is enabled.
- `solver.save()` stores only model and optimizer state. It does not store the JSON config; save `solver.config_dict()` separately when you need reproducible reconstruction.

## Scheduler Or Metric Surprises

Symptoms:

- Scheduler steps more or less often than expected.
- Metrics only appear after many batches.
- Multi-GPU metrics differ from single-GPU metrics.

Checks and fixes:

- Engine calls `scheduler.step()` once after each training epoch, not each batch.
- `log_interval` counts optimizer updates, not raw batches. With `gradient_interval > 1`, logs appear less frequently in raw batch terms.
- Engine averages metrics collected within a gradient interval before logging.
- In distributed training, Engine reduces training metrics across processes and concatenates evaluation predictions/targets before computing metrics.
- If `batch_per_epoch` is set, each epoch only consumes that many dataloader batches.
