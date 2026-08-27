# Training Utility API

This reference summarizes Scenic training APIs that are safe to reason about
without launching a training loop. Use it for questions about learning-rate
schedules, optimizers, train state, checkpoint helpers, generic trainers, and
transfer/pretraining caveats.

## Learning-rate schedules

Primary entry point:

```python
from scenic.train_lib import lr_schedules
lr_fn = lr_schedules.get_learning_rate_fn(config)
value = lr_fn(step)
```

`get_learning_rate_fn(config)` expects `config.lr_configs` and requires
`config.lr_configs.base_learning_rate`. If `learning_rate_schedule` is absent,
it returns a constant schedule equal to `base_learning_rate`. If
`learning_rate_schedule` is present, the central implementation recognizes the
`compound` schedule.

`compound` multiplies factors named in `config.lr_configs.factors`, separated by
`*`. Supported factor names and important keys:

| Factor | Required / useful keys | Notes |
| --- | --- | --- |
| `constant` | `base_learning_rate` | Multiplies by the base LR. |
| `linear_warmup` | `warmup_steps`; optional `warmup_alpha` | Warms from `warmup_alpha` fraction to 1.0 over `warmup_steps`. |
| `polynomial` | `decay_steps`, `end_factor`, `power` | Polynomial decay factor. |
| `piecewise_constant` | `decay_events`, `decay_factors` | Decay factors are absolute ratios from the initial LR, not relative chained multipliers. |
| `piecewise_linear` | `decay_events`, `decay_factors` | Linearly interpolates between absolute ratios. |
| `rsqrt_decay` | optional `warmup_steps`, `timescale` | Inverse-square-root style decay after warmup. |
| `decay_every` | `steps_per_decay`, `decay_factor` | Multiplicative decay every fixed number of steps. |
| `exponential_decay` | `decay_steps`, `decay_rate`; optional `staircase` | TensorFlow-style exponential decay. |
| `cosine_decay` | `steps_per_cycle`; optional `t_mul`, `m_mul`, `alpha`, `warmup_steps`, `total_steps`, `start_decay_step` | `steps_per_cycle` must be positive; supports restarts and warmup adjustment. |
| `linear_decay` | `total_steps`; optional `warmup_steps`, `end_learning_rate` | Requires `total_steps > warmup_steps`. |
| `linear_cooldown` | `total_steps`, `cooldown_steps`; optional `warmup_steps` | Reduces LR near the end of training. |

Unknown factors raise `ValueError`. Because LR functions use JAX arrays, a
configuration can be checked without data or model construction:

```python
lr_fn = lr_schedules.get_learning_rate_fn(config)
print(float(lr_fn(0)))
print(float(lr_fn(100)))
```

## Optimizer configuration

Primary entry points:

```python
from scenic.train_lib import optimizers
optimizer_config = optimizers.get_optax_optimizer_config(config)
tx = optimizers.get_optimizer(optimizer_config, learning_rate_fn, params=params)
```

`get_optax_optimizer_config(config)` supports two config styles:

- New style: `config.optimizer_configs.optimizer = 'adamw'` plus optax kwargs.
- Backward-compatible style: top-level `config.optimizer = 'adam'`,
  `'momentum'`, `'nesterov'`, `'sgd'`, etc. The helper copies and translates
  those names into optax-compatible config.

Do not define both top-level `optimizer` and
`optimizer_configs.optimizer`; the helper raises a `ValueError` to prevent
contradictory optimizer choices.

Backward-compatible translations:

| Scenic-style key | Optax-style result |
| --- | --- |
| `optimizer='adam'` with `weight_decay` | Uses `adamw` semantics. |
| `optimizer='momentum'` | Uses `sgd`; if no momentum is supplied, inserts `momentum=0.9`. |
| `optimizer='nesterov'` | Uses `sgd` with `nesterov=True`. |
| `beta1`, `beta2`, `epsilon` | Renamed to optax `b1`, `b2`, `eps`. |
| `grad_clip_configs` | Moved to `optimizer_config.grad_clip`. |

`get_optimizer(optimizer_config, learning_rate_fn, params=None)` constructs an
`optax.GradientTransformation`. It deep-copies the config, handles Scenic
special fields, then calls `getattr(optax, optimizer_name)(learning_rate=..., **kwargs)`.
Misspelled optimizer kwargs therefore fail early instead of being silently
ignored.

Special optimizer fields:

| Field | Behavior |
| --- | --- |
| `weight_decay` | For SGD, prepends `optax.add_decayed_weights`; for AdamW/LAMB/AdamaxW/Adafactor/LARS it passes masks in the form expected by the optimizer. |
| `skip_scale_and_bias_regularization=True` | Skips weight decay for 1-D parameters such as scale and bias. Requires `params`. |
| `grad_clip.clip_method` and `grad_clip.clip_value` | Supports `clip_by_global_norm`, `adaptive_grad_clip`, `clip`, and `clip_by_block_rms`. |
| `freeze_params_reg_exp` | Freezes parameters whose slash-separated leaf name matches a regex. Requires `params`; raises if the regex freezes every parameter. |

If a user wants a no-training optimizer check, build a tiny dummy parameter tree
or pass real initialized params if available. Do not call the trainer just to
validate optimizer spelling.

## TrainState and checkpoint concepts

`train_utils.TrainState` is a Flax `struct.dataclass` designed to be used inside
JAX transformations and checkpointing. Fields:

| Field | Meaning |
| --- | --- |
| `tx` | Optional optax `GradientTransformation`; non-pytree metadata. |
| `opt_state` | Optimizer state. |
| `params` | Model parameters. |
| `global_step` | Current training step. |
| `model_state` | Non-parameter model state such as batch statistics. |
| `rng` | Training RNG key. |
| `metadata` | Extra checkpoint metadata, often including `Chrono` timing state. |

Useful helpers:

- `train_utils.initialize_model(...)` and
  `initialize_model_with_pytree(...)`: build dummy inputs from model input specs,
  initialize Flax variables on CPU, optionally count FLOPs, and return params,
  model state, parameter count, and GFLOPs.
- `train_utils.get_dataset(...)`: resolves `config.dataset_name`, checks
  train/eval batch divisibility by JAX device count, enforces dataset-service
  seeding rules, and calls the dataset builder.
- `train_utils.get_num_training_steps(config, dataset_meta_data)`: uses exactly
  one of `num_training_steps` or `num_training_epochs`; epoch-based configs need
  `num_train_examples` in dataset metadata.
- `train_utils.save_checkpoint(workdir, train_state, max_to_keep=3)`: writes a
  Flax checkpoint from process 0.
- `train_utils.restore_checkpoint(checkpoint_path, train_state, assert_exist=False, step=None)`:
  restores into an existing Scenic `TrainState`; use pretraining helpers when
  no target TrainState exists yet.
- `train_utils.checkpoint_path_step(path)`: extracts the numeric step from a
  checkpoint path string.
- `train_utils.handle_checkpointing(train_state, chrono, workdir, max_checkpoints_to_keep=3)`:
  syncs model state across replicas, unreplicates, stores timing metadata, and
  writes the checkpoint.
- `train_utils.bind_rng_to_host_device(rng, axis_name, bind_to)`: folds RNG by
  host or device inside a pmapped function for dropout/mixup randomness.
- `train_utils.log_train_summary` and `log_eval_summary`: aggregate `(value,
  normalizer)` metric pairs and write CLU summaries; NaN train metrics raise
  `TrainingDivergedError`.

## Generic trainer flow

The central trainer registry maps these names:

| `config.trainer_name` | Trainer |
| --- | --- |
| `classification_trainer` | Standard classification train/eval loop. |
| `transfer_trainer` | Classification-style loop with optional pretraining, few-shot, and representation utilities. |

The trainer function signature is keyword-only:

```python
train_state, train_summary, eval_summary = train_fn(
    rng=rng,
    config=config,
    model_cls=model_cls,
    dataset=dataset,
    workdir=workdir,
    writer=writer,
)
```

The standard classification trainer performs this sequence:

1. Instantiate `model = model_cls(config, dataset.meta_data)`.
2. Initialize model params/state from `dataset.meta_data['input_shape']` and
   optional `input_dtype`.
3. Build LR schedule, optimizer config, optax transformation, and optimizer
   state.
4. Create `TrainState(global_step=0, params, model_state, opt_state, tx, rng,
   metadata={'chrono': ...})`.
5. If `config.checkpoint` is true, restore from `workdir`.
6. Replicate state across devices.
7. Determine total steps from `num_training_steps` or `num_training_epochs`.
8. Create pmapped train/eval steps with axis name `batch`.
9. Iterate batches, log train/eval summaries, optionally profile, and save
   checkpoints.
10. Synchronize hosts at the end and return final summaries for regression
    checks.

Required dataset object shape for generic trainers:

- `dataset.train_iter` yields training batches with at least `inputs` and labels
  expected by the model's loss/metrics.
- `dataset.valid_iter` yields evaluation batches.
- `dataset.meta_data` includes `input_shape`, optional `input_dtype`,
  `num_eval_examples`, and for epoch-based training `num_train_examples`.

## Transfer and pretraining caveats

Transfer training adds optional behavior on top of the classification flow:

- If `start_step == 0` and `config.init_from.checkpoint_path` exists,
  `pretrain_utils.restore_pretrained_checkpoint(..., assert_exist=True)` loads
  pretrained params before training.
- `config.init_from.model_config`, checkpoint prefix/model prefix mappings, and
  skip regexes may be needed when checkpoint parameter names differ from the
  target model.
- Transfer utilities can compute representations for few-shot or linear-probe
  evaluation using a named layer. A missing layer name raises a `ValueError`.

`pretrain_utils` can restore Scenic TrainState checkpoints, inspect missing or
extra parameter keys, initialize from a pretrain state, and convert BigVision
checkpoint formats. BigVision conversion intentionally does not restore optimizer
state; it restores model weights, global step, and available training-time
metadata.

Important dependency caveat: the trainer registry import can fail in modern
TensorFlow/Keras environments because the transfer path may import BigVision and
TensorFlow Addons, and some TensorFlow Addons releases import internal Keras
modules such as `keras.src.engine`. For config, LR, optimizer, or TrainState
questions, avoid importing `scenic.train_lib.trainers`. For actual central-main
training, resolve the optional dependency pinning first; see
[troubleshooting.md](troubleshooting.md).

## Source scripts and verification anchors

No original Scenic source script is copied into this sub-skill. The reason is
that the installed `scenic.main` Python module is the runtime entry point, while
copying a source launcher would couple the skill to a checkout layout and could
accidentally launch training. The bundled `scenic_config_probe.py` is a safe
replacement for config inspection because it never calls the trainer.

Native verification anchors for this sub-skill are the learning-rate schedule,
optimizer, train-utils Chrono, and classification-trainer test modules. Treat
those tests as integration verification candidates only; do not make them a
runtime dependency and do not ask users to run them just to answer a config or
launch-safety question.
