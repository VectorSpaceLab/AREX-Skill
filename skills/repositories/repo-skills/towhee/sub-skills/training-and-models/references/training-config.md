# Training configuration and Trainer

Towhee's training layer is an optional PyTorch-oriented helper stack. Use it only after the target environment intentionally has PyTorch, TorchVision when image examples/models need it, TorchMetrics, and YAML support. For a no-import config stub, use [../scripts/training_config_template.py](../scripts/training_config_template.py).

## Core objects

| Object | Use for | Key contract |
|---|---|---|
| `TrainingConfig` | Structured training configuration that can be saved to or loaded from YAML. | Fields are grouped into YAML sections such as `train`, `learning`, `metrics`, `logging`, `callback`, and `device`. |
| `Trainer` | Training a `torch.nn.Module` with Towhee's default loss/metric/optimizer/scheduler callbacks. | Requires a model. Training requires a `train_dataset` or `train_dataloader`. Default loss/metric logic assumes each batch is `(inputs, labels)`. |
| `NNOperator.train(...)` | Convenience bridge from an `NNOperator` to `Trainer.train(...)`. | Calls `setup_trainer(...)` first, then trains through `self.trainer`. |
| `NNOperator.setup_trainer(...)` | Attaches or updates a `Trainer` on the operator. | The operator must expose `self.model` or `self._model` as a `torch.nn.Module`. |

## Minimal YAML shape

`TrainingConfig.save_to_yaml(...)` writes category sections. `load_from_yaml(...)` reads the same sections and ignores unknown sections with a warning. Keep keys as Towhee field names with underscores, not dashed names.

```yaml
train:
  output_dir: ./towhee-training-output
  overwrite_output_dir: true
  eval_strategy: no
  eval_steps: null
  batch_size: 2
  val_batch_size: -1
  seed: 42
  epoch_num: 1
  dataloader_pin_memory: false
  dataloader_drop_last: false
  dataloader_num_workers: 0
  print_steps: 1
  load_best_model_at_end: false
  freeze_bn: false
learning:
  loss: CrossEntropyLoss
  optimizer:
    name_: AdamW
    lr: 0.001
  lr_scheduler_type: linear
  warmup_ratio: 0.0
  warmup_steps: 0
metrics:
  metric: Accuracy
logging: {}
callback:
  early_stopping: no
  model_checkpoint: no
  tensorboard: null
device:
  device_str: cpu
```

Use `tensorboard: null`, `early_stopping: no`, or `model_checkpoint: no` to disable optional callbacks. Towhee treats `"no"`, `"null"`, `"None"`, `None`, and `False` as disabled callback/config values in several trainer paths.

## Important `TrainingConfig` fields

| Category | Fields and notes |
|---|---|
| `train` | `output_dir`, `overwrite_output_dir`, `eval_strategy` (`steps`, `step`, `epoch`, `eval_epoch`, `no`), `eval_steps`, `batch_size`, `val_batch_size`, `seed`, `epoch_num`, dataloader flags, `print_steps`, `load_best_model_at_end`, `freeze_bn`. |
| `learning` | `lr`, `loss`, `optimizer`, `lr_scheduler_type`, `warmup_ratio`, `warmup_steps`. |
| `metrics` | `metric`, usually a TorchMetrics-compatible name such as the default `Accuracy`; override `compute_metric(...)` for custom tasks. |
| `callback` | `early_stopping`, `model_checkpoint`, `tensorboard`; each may be a dict of callback kwargs or a disabled value. |
| `device` | `device_str`; `null` auto-selects `cuda:0` when CUDA is available, otherwise CPU. |

`train_batch_size` asserts `batch_size > 0`. `eval_batch_size` uses `batch_size` when `val_batch_size == -1`.

## Loss, optimizer, and scheduler naming

Towhee constructs default training components from strings or dictionaries:

- `loss`: string class name from `torch.nn.modules.loss`, for example `CrossEntropyLoss`, or a dict with `name_` plus constructor kwargs.
- `optimizer`: string class name from `torch.optim`, for example `Adam`, `AdamW`, or `SGD`, or a dict with `name_` plus constructor kwargs. The optimizer is built from parameters where `requires_grad` is true.
- `lr_scheduler_type`: either one of Towhee's built-in scheduler strings (`linear`, `cosine`, `cosine_with_restarts`, `polynomial`, `constant`, `constant_with_warmup`) or a dict for `torch.optim.lr_scheduler` with `name_` and scheduler kwargs, such as `name_: StepLR`, `step_size: 3`, `gamma: 0.5`.

When a scheduler is one of Towhee's built-in strings, warmup is computed from `warmup_steps` if it is positive; otherwise from `ceil(num_training_steps * warmup_ratio)`. The `constant` scheduler does not need warmup or total-step values; the other built-in scheduler names do.

For custom objects, create a `Trainer` and call:

```python
trainer.set_loss(custom_loss, loss_name='my_loss')
trainer.set_optimizer(custom_optimizer, optimizer_name='my_optimizer')
```

## Device behavior

- `device_str: null`: choose `cuda:0` if `torch.cuda.is_available()` is true, otherwise `cpu`.
- `device_str: cpu`: force CPU and avoid CUDA assumptions.
- `device_str: cuda:N`: use one selected GPU device.
- `device_str: cuda`: wrap the model in `torch.nn.DataParallel` over visible GPUs. Use the host's CUDA visibility controls before launch if only a subset should be visible.

Prefer `cpu` in examples, templates, and diagnosis unless the user explicitly requested GPU training and the environment is prepared for it.

## Trainer workflow

1. Build or load a `TrainingConfig`.
2. Prepare a `torch.nn.Module` and a dataset/dataloader. Default `Trainer.compute_loss(...)` expects batches shaped like `(features, labels)`, runs `outputs = model(features)`, and computes `loss(outputs, labels)`.
3. Create `Trainer(model, training_config, train_dataset=..., eval_dataset=...)` or pass dataloaders directly.
4. Call `trainer.train(resume_checkpoint_path=None)`.
5. Use `trainer.save(path)` or inspect saved epoch/final checkpoints.

During training, Towhee sets seeds, moves inputs to `configs.device`, creates optimizer/loss/metric/scheduler/callbacks, optionally evaluates at step or epoch boundaries, saves `epoch_N` checkpoints when checkpointing is enabled, and always saves a `final_epoch` folder. Checkpoints contain model weights, trainer state, and a model-card README when a `ModelCard` is available.

Subclass `Trainer` and override `compute_loss(...)` and often `compute_metric(...)` when a task does not use `(input_tensor, label_tensor)` batches or a single classification-style metric.

## NNOperator training bridge

`NNOperator.train(training_config=None, train_dataset=None, eval_dataset=None, resume_checkpoint_path=None, **kwargs)` calls:

```python
self.setup_trainer(training_config, train_dataset, eval_dataset, **kwargs)
self.trainer.train(resume_checkpoint_path)
```

`setup_trainer(...)` creates a `Trainer` on first use and updates its config/datasets/dataloaders/model card on later calls. Before calling it, make sure the operator has one of:

```python
self.model = some_torch_module
# or
self._model = some_torch_module
```

If neither attribute is a `torch.nn.Module`, Towhee raises `AttributeError: There is no trainable model attr in this operator.`

## Dataset and model-card notes

- `Trainer` accepts ordinary `torch.utils.data.Dataset` objects, Towhee's `TowheeDataSet` wrappers, or explicit dataloaders.
- `TorchDataSet` is a thin wrapper around a PyTorch dataset and exposes the wrapped object through `.dataset`.
- Towhee's image-training helper expects image files plus a CSV with `image_name` and `category` columns, and requires image/Pandas/TorchVision dependencies.
- `ModelCard` is optional. If absent, Towhee creates one, fills the model name from the model class, records model architecture and training config, then writes model-card data with checkpoints.

Use the `data-utilities` sub-skill for non-training data wrappers, media types, and serialization patterns.
