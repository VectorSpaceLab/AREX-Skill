# Running and Training Troubleshooting

Use this reference to triage Scenic launch, config, trainer-import, backend, and
checkpoint/pretraining failures while avoiding accidental expensive training.

## First response checklist

1. **Do not launch training yet** if the user only asks whether a config is safe.
   Run `python scripts/scenic_config_probe.py CONFIG` instead.
2. **Check lightweight imports** before trainer imports:
   `scenic`, `jax`, `scenic.train_lib.lr_schedules`,
   `scenic.train_lib.optimizers`, and `scenic.train_lib.train_utils`.
3. **Classify the failure**: config shape, missing dataset/model/trainer name,
   optional dependency mismatch, accelerator/backend issue, data absence,
   checkpoint/pretraining issue, or expected full-training cost.
4. **Route narrowly**: model registry/API issues go to modeling-and-layers;
   dataset registry/layout issues go to data-pipelines; project-specific
   optional dependencies and tools go to baselines-and-projects.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'scenic'` | Scenic is not installed in the active Python environment. | Install the package in the intended environment, then re-run a lightweight import check. Avoid mutating a shared environment if version changes are needed. |
| JAX imports but no accelerator appears | CPU-only `jaxlib`, incompatible CUDA/driver, or forced CPU env vars. | For CPU preflight use `JAX_PLATFORMS=cpu`. For GPU training, install the JAX/JAXLIB build matching the machine's CUDA stack and verify `jax.devices()` before launch. |
| TensorFlow grabs GPU memory before JAX | TensorFlow imported outside the Scenic app wrapper or by a custom script. | The Scenic app wrapper hides TensorFlow GPU devices before calling main. For custom probes, avoid TensorFlow-heavy imports or set memory/visibility policy before importing TF pipelines. |
| `pip install .` fails around optional project packages | Broad project/testing extras pull heavy or incompatible packages. | Install only core Scenic for running/config/training utilities. Add project extras only for the selected project workflow. |
| `optax` install/version trouble | Scenic's packaging can require a recent Optax variant. | Use a fresh environment and install a compatible Optax release/source matching the Scenic checkout and JAX version. Do not downgrade a shared environment without user approval. |

## Config flag and shape errors

| Symptom | Meaning | Fix |
| --- | --- | --- |
| Required flag error for `--config` or `--workdir` | The generic runner requires both flags. | Supply a trusted Python config file and an experiment workdir. |
| Config file imports but `get_config` is missing | ml-collections config flags expect a config factory. | Add/choose a config module with `get_config(...)` returning a `ConfigDict`, or use the project-specific entry point documented by that project. |
| `rng_seed` missing | `scenic.app` creates `jax.random.PRNGKey(config.rng_seed)`. | Add an integer `rng_seed`. |
| `model_name`, `dataset_name`, or `trainer_name` missing | `scenic.main` needs these to resolve the model, dataset, and trainer. | Add the missing key or route to the appropriate model/data/project sub-skill to select the right name. |
| `batch_size` or `eval_batch_size` not divisible by device count | `train_utils.get_dataset` enforces device sharding. | Lower batch size, change eval batch size, or adjust visible devices. For CPU local smoke tests, use a small batch divisible by `jax.device_count()`. |
| Both `num_training_steps` and `num_training_epochs` are set | Generic training length helper requires exactly one. | Keep one source of total steps. For smoke runs, prefer a tiny `num_training_steps`. |
| Neither `num_training_steps` nor `num_training_epochs` is set | Trainer cannot determine total training steps. | Add one. Epoch-based configs also require dataset metadata with `num_train_examples`. |
| `base_learning_rate` missing | LR builder requires `config.lr_configs.base_learning_rate`. | Add it, even when using a compound schedule. |
| Unknown LR factor | `compound` schedule saw a factor name it does not implement. | Use one of the documented factor names in `training-api.md` and add its required keys. |
| LR schedule tests fail at `tf.keras.experimental.CosineDecayRestarts` | Modern TensorFlow/Keras stacks removed or relocated the legacy `tf.keras.experimental` namespace used by older Scenic tests for comparison. | Treat this as a TensorFlow/Keras compatibility issue, not an LR-schedule logic claim by itself. Pin a compatible TensorFlow/Keras generation for native test runs, or validate the Scenic LR function directly for config/API preflight. |
| Invalid optimizer kwarg raises `TypeError` | Optimizer configs are passed directly to optax after Scenic special-field handling. | Fix spelling or use the optax-compatible key name. |
| Both top-level `optimizer` and `optimizer_configs.optimizer` are defined | Scenic rejects contradictory old/new style optimizer config. | Use only one style. |

## Dataset, model, and trainer name errors

| Error | Triage |
| --- | --- |
| `Unrecognized trainer: ...` | The central trainer registry recognizes `classification_trainer` and `transfer_trainer`. If the user is using a project-specific trainer, route to the project-specific entry point instead of central `scenic.main`. |
| Unknown model name | Route to modeling-and-layers for model registry names and BaseModel contracts. Confirm the config's `model_name` is registered in the installed package. |
| Unknown dataset name | Route to data-pipelines for dataset registry names, lazy imports, TFDS/raw-data requirements, and dataset config shape. |
| Dataset service plus fixed shuffle seed | `train_utils.get_dataset` rejects this because each worker would produce identical randomized data. | Set `config.shuffle_seed = None` when using `--dataset_service_address`, or do not use dataset service. |
| Dataset download/data-not-found failure | The config reached data construction; this is not a config-shape failure. | Confirm TFDS/raw-data availability and layout through data-pipelines before relaunch. |

## `tensorflow_addons`, `keras.src.engine`, `big_vision`, and trainer imports

The central trainer registry imports both classification and transfer trainers.
The transfer path can import BigVision and TensorFlow Addons. In modern
TensorFlow/Keras environments, TensorFlow Addons may fail with errors such as:

```text
ModuleNotFoundError: No module named 'keras.src.engine'
```

or compatibility warnings/errors involving TensorFlow Addons and Keras.

Recovery pattern:

1. If the user only needs config, LR, optimizer, or TrainState help, avoid the
   trainer registry entirely. Use the bundled config probe and import
   `lr_schedules`, `optimizers`, or `train_utils` directly.
2. If the user wants central `scenic.main` training, the trainer registry import
   is unavoidable. Use a fresh environment with a mutually compatible
   TensorFlow, TensorFlow Addons, and Keras set. In practice, avoid standalone
   Keras 3 for TensorFlow Addons releases that expect pre-Keras-3 internals;
   pair TensorFlow Addons with the TensorFlow/Keras generation it supports.
3. If transfer/pretraining or BigVision checkpoint conversion is not needed,
   do not install or import those optional paths for simple utility checks.
   However, remember that central-main training still imports the registry, so a
   broken transfer dependency can block even classification launches.
4. Do not downgrade or reinstall TensorFlow/Keras/TFA inside a user-provided
   shared environment without explicit approval. Create a fresh private env when
   dependency repair is required.

## JAX backend and launch environment issues

| Symptom | Recovery |
| --- | --- |
| CPU preflight should not touch GPU | Prefix the command with `JAX_PLATFORMS=cpu` and keep the run to config/LR/optimizer checks. |
| GPU training OOMs before first step | Ensure TensorFlow GPU visibility is hidden by using the Scenic app runner; consider `XLA_PYTHON_CLIENT_PREALLOCATE=false`; reduce batch size; check that no other process holds memory. |
| `jax_backend_target` / `jax_xla_backend` confusion | These are absl/JAX flags exposed by the app wrapper. Use them only when a remote backend or specialized runtime requires them; ordinary CPU/GPU local runs usually do not. |
| Multi-host hang at exit | Generic trainers call a host barrier at the end. If hosts are misconfigured or one fails early, others can wait. Check logs on every host and stop the whole job together. |
| First step appears slow | Generic trainers use JAX `pmap`; the first train/eval step compiles. This is expected, but full-size configs can make compilation and memory use expensive. |

## Checkpoint and pretraining issues

| Symptom | Likely cause and fix |
| --- | --- |
| Job resumes unexpectedly | `config.checkpoint=True` and workdir contains checkpoints. Use a fresh workdir for new experiments, or disable checkpointing only for intentional smoke tests. |
| `No checkpoint for the pretrained model is found` | Transfer/pretraining path was configured with `assert_exist=True` and the checkpoint path is wrong or unavailable. Confirm path/access before launch. |
| Restore without target TrainState fails | Generic checkpoint restore expects a Scenic `TrainState`; pretraining restore helpers handle checkpoint-only loading before inserting params into a target state. |
| Missing/extra parameter warnings | Checkpoint params do not exactly match target model params. Use model-specific init-from mapping, prefix paths, or skip regex only when the user understands what will be loaded. |
| BigVision conversion loses optimizer state | BigVision conversion restores model weights and global step but intentionally does not restore optimizer state. Treat it as initialization/transfer, not exact training resume. |

## Expensive-training stop conditions

Stop and ask for confirmation before launch when any of these are true:

- The config is ImageNet-scale, multi-host, long-epoch, or has a very large
  batch size.
- The user only asked for validation, review, or debugging, not actual training.
- Dataset availability, data layout, or credentials are unknown.
- The workdir contains checkpoints and resume vs. fresh-start intent is unclear.
- `config.init_from` points to a large external checkpoint or requires BigVision
  conversion.
- The command would install/downgrade TensorFlow, Keras, TensorFlow Addons, JAX,
  or CUDA packages in a shared environment.
- GPU/TPU availability is unknown and CPU fallback would make the run
  impractically slow.

For a safe smoke-style run, prefer a dedicated tiny config or a config argument
that explicitly switches to local settings, set a fresh temporary workdir, use a
small batch divisible by the visible device count, set a small
`num_training_steps`, disable profiling (`xprof=False`) when possible, and keep
checkpointing off unless checkpoint behavior is the target of the test.

## Synthetic usability cases this sub-skill covers

- **Config preflight**: a user gives a config and asks if it is safe to launch.
  Use `scripts/scenic_config_probe.py` to report missing `rng_seed`,
  `dataset_name`, `model_name`, `trainer_name`, batch/training-length, LR, and
  optimizer fields without importing trainers or starting data/model work.
- **Trainer import failure**: a user sees `tensorflow_addons` or
  `keras.src.engine` while importing trainers. Explain the transfer/BigVision
  optional dependency path, avoid trainer imports for utility checks, and fix
  TF/TFA/Keras compatibility in a fresh environment before central-main
  training.
