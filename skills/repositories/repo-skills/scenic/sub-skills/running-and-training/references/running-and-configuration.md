# Running and Configuration

This reference explains Scenic's generic app runner and how to validate and
launch a config safely. It is for runtime use; it does not require access to a
source checkout.

## What the Scenic app runner does

`scenic.app.run(main)` is the common wrapper used by Scenic entry points.
It defines the general absl/ml-collections flags below and then calls the user
`main` as:

```python
main(rng=<jax PRNGKey>, config=<ml_collections.ConfigDict>, workdir=<str>, writer=<CLU MetricWriter>)
```

General runner flags:

| Flag | Required | Meaning |
| --- | --- | --- |
| `--config=/path/to/config.py` | yes | Python config file loaded by `ml_collections.config_flags.DEFINE_config_file`; it should define `get_config(...)` returning a `ConfigDict`. |
| `--workdir=/path/to/workdir` | yes | Experiment directory for summaries, profile output, and checkpoints. If the config contains `workdir_suffix`, the runner appends it to the supplied workdir. |
| `--dataset_service_address=...` | no | Optional tf.data service address passed to dataset construction. Use only when the config is compatible with dataset service seeding. |
| `--jax_backend_target=...` | no | Exposed through `jax.config.config_with_absl()` for remote/back-end-specific JAX runtimes. |
| `--jax_xla_backend=...` | no | Exposed through `jax.config.config_with_absl()` for JAX XLA backend selection. |

Before calling `main`, the wrapper hides TensorFlow GPU devices so TensorFlow
input-pipeline imports do not reserve accelerator memory that JAX needs. It
enables Flax named calls for profiling, logs JAX host/device information,
creates a CLU default metric writer, builds `rng = jax.random.PRNGKey(config.rng_seed)`,
and passes that RNG into the main function.

## What the generic Scenic main does

The central `scenic.main` flow is:

1. Resolve the model class from `config.model_name`.
2. Split the runner RNG into data and training RNGs.
3. If `config.checkpoint` is true and a checkpoint exists in `workdir`, fold the
   restored global step into the dataset RNG so resumed jobs do not repeat the
   same deterministic example order.
4. Build the dataset with `train_utils.get_dataset(config, data_rng,
   dataset_service_address=FLAGS.dataset_service_address)`.
5. Resolve the trainer from `config.trainer_name` and call it with
   `rng`, `config`, `model_cls`, `dataset`, `workdir`, and `writer`.

This means a config can import successfully but still be unsafe to launch if it
is missing runner, model, dataset, trainer, or training-loop fields.

## Direct install/import checks

For a fresh environment, install Scenic into the intended Python environment and
verify the lightweight training utility imports before any training launch:

```bash
python -m pip install .
python - <<'PY'
import scenic
import jax
from scenic.train_lib import lr_schedules, optimizers, train_utils
print('scenic package import: ok')
print('jax devices:', jax.devices())
print('train utils:', train_utils.TrainState.__name__)
PY
```

Do not use `from scenic.train_lib import trainers` as the first health check:
that import also loads transfer/pretraining utilities and can fail when optional
TensorFlow Addons / BigVision / Keras dependencies are incompatible. See
[troubleshooting.md](troubleshooting.md) before treating that as a core install
failure.

## Safe config preflight without training

When the user provides a config file, run the bundled helper first:

```bash
python scripts/scenic_config_probe.py /path/to/config.py
```

If the config's `get_config` needs a string argument, pass it explicitly:

```bash
python scripts/scenic_config_probe.py /path/to/config.py --config-arg runlocal
```

The probe imports the config module, calls `get_config`, prints top-level keys,
checks key runner/training fields, and exits without importing Scenic trainers,
building datasets, initializing models, or entering a training loop.

Use the result as a launch gate:

- **ERROR** entries mean the generic Scenic runner or trainer is likely to fail
  before useful training. Fix them before launch.
- **WARN** entries are launch risks: full-scale configs, absent `dataset_configs`,
  missing optional logging/checkpoint knobs, trainer import caveats, or fields
  that are only required for a selected workflow.
- A clean probe does **not** prove data availability, model shape correctness,
  accelerator compatibility, or checkpoint compatibility. It only proves basic
  config shape and importability.

Config files are Python. Only preflight configs from trusted sources.

## Minimum config shape for `scenic.main`

| Area | Common keys | Why they matter |
| --- | --- | --- |
| Runner/RNG | `rng_seed`; optional `workdir_suffix` | `scenic.app` constructs a JAX PRNGKey from `rng_seed`; `workdir_suffix` modifies the runtime workdir. |
| Dataset | `dataset_name`, `dataset_configs`, `data_dtype_str`, `batch_size`, optional `eval_batch_size`, `shuffle_seed` | `train_utils.get_dataset` resolves the dataset builder, checks batch divisibility by device count, chooses dtypes, and passes dataset configs/service address. |
| Model | `model_name`, often `model`, `model_dtype_str`, model-specific fields | `scenic.main` resolves the model class from `model_name`; the model constructor consumes model-specific keys. |
| Trainer | `trainer_name` | The central trainer registry recognizes `classification_trainer` and `transfer_trainer`; project-specific entry points may define their own trainers. |
| Training length | exactly one of `num_training_steps` or `num_training_epochs` | `train_utils.get_num_training_steps` requires a single source of total steps; epoch-based configs also require dataset metadata with `num_train_examples`. |
| Learning rate | `lr_configs.base_learning_rate`; optional `lr_configs.learning_rate_schedule`, `lr_configs.factors`, schedule-specific keys | `lr_schedules.get_learning_rate_fn` requires `base_learning_rate`; compound schedules require all keys named by the selected factors. |
| Optimizer | either top-level `optimizer` or `optimizer_configs.optimizer` plus optimizer-specific kwargs | `optimizers.get_optax_optimizer_config` rejects contradictory old/new style optimizer declarations. |
| Logging/eval/checkpoint | `checkpoint`, `debug_train`, `debug_eval`; optional `log_eval_steps`, `log_summary_steps`, `checkpoint_steps`, `max_checkpoint_keep`, `xprof`, `write_summary` | Generic trainers access these fields directly or through defaults. Missing debug/checkpoint booleans commonly cause early errors. |

Representative patterns:

- A small MNIST-style config uses `dataset_name='mnist'`,
  `model_name='fully_connected_classification'`,
  `trainer_name='classification_trainer'`, constant LR, top-level
  `optimizer='momentum'`, `optimizer_configs.momentum=0.9`, `batch_size=128`,
  `rng_seed=0`, and `checkpoint=True`.
- A ViT/ImageNet-style config uses `model_name='vit_multilabel_classification'`,
  a nested `model` config, `trainer_name='classification_trainer'`, Adam-style
  optimizer settings, `factors='constant*linear_warmup*cosine_decay'`, a large
  default batch/epoch count, and an optional config argument that switches to a
  smaller local batch.

## Constructing a training command

Use direct Python module invocation after Scenic is installed:

```bash
CONFIG=/path/to/config.py
WORKDIR=/path/to/new-or-intentional-resume-workdir
mkdir -p "$WORKDIR"
python -m scenic.main \
  --config="$CONFIG" \
  --workdir="$WORKDIR"
```

Some launcher snippets place a standalone `--` before application flags. For a
direct `python -m scenic.main` command, absl parses flags before a standalone
separator, so the safe default is to omit the separator unless the user's
launcher specifically requires it and has been verified.

Add a config-string argument only when the config's `get_config` supports it.
With ml-collections config flags this is commonly encoded after a colon:

```bash
python -m scenic.main \
  --config="/path/to/config.py:runlocal" \
  --workdir="$WORKDIR"
```

For CPU-only preflight or small local runs:

```bash
JAX_PLATFORMS=cpu XLA_PYTHON_CLIENT_PREALLOCATE=false \
python -m scenic.main \
  --config="$CONFIG" \
  --workdir="$WORKDIR"
```

For a tf.data service run, pass the service address and ensure the config does
not set a fixed `shuffle_seed`:

```bash
python -m scenic.main \
  --config="$CONFIG" \
  --workdir="$WORKDIR" \
  --dataset_service_address="grpc://HOST:PORT"
```

`train_utils.get_dataset` raises if a dataset service address is combined with a
non-`None` `shuffle_seed`, because every worker would otherwise produce the same
randomized data.

## Workdir and checkpoint behavior

- `--workdir` is required even if checkpointing is disabled, because summary
  writers and profiling hooks use it.
- If `config.workdir_suffix` exists, the actual workdir is
  `os.path.join(flag_workdir, config.workdir_suffix)`.
- If `config.checkpoint` is true, generic trainers restore from the latest
  checkpoint in the workdir before training and save checkpoints at
  `checkpoint_steps` or eval-step intervals; only the lead host writes them.
- When a resume checkpoint is found, the main function folds the checkpoint step
  into the dataset RNG. This changes deterministic example order after resume.
- Use a fresh workdir for a new experiment. Use an existing workdir only when
  the user explicitly wants resume behavior.

## No-training validation sequence

1. Run `python scripts/scenic_config_probe.py CONFIG`.
2. Check lightweight imports of `scenic`, `jax`, `lr_schedules`, `optimizers`,
   and `train_utils`.
3. If the user only asks about LR/optimizer shape, instantiate those utilities
   directly from the config; do not import trainer registry or datasets.
4. If the user asks to launch, confirm data availability, workdir intent,
   expected runtime, accelerator availability, batch/device divisibility, and
   checkpoint/pretraining paths before running `scenic.main`.
5. Stop and ask before launching full ImageNet-scale, multi-host, or
   checkpoint-converting jobs unless the user already approved that cost.
