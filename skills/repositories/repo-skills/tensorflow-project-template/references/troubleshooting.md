# Troubleshooting

## Purpose

Read this when a TensorFlow Project Template checkout or copied project fails to import, parse config, run the example graph, write summaries, or save/load checkpoints.

## Fast triage

1. Run the static checker from this skill:

   ```bash
   python scripts/check_template_static.py --repo-root /path/to/template-copy
   ```

2. If TensorFlow 1.x is available, run the bounded smoke:

   ```bash
   python scripts/run_tiny_training_smoke.py --repo-root /path/to/template-copy --work-dir /path/to/safe-smoke-workdir
   ```

3. If the static check passes but the smoke fails, use the symptom table below.

## Import and dependency failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'base'` or `models` | The project root is not on `PYTHONPATH`, or the process was started from the wrong directory. | Run from the project root, set `PYTHONPATH` to the project root, or add the project root to `sys.path` in a wrapper script. |
| `ModuleNotFoundError: No module named 'tensorflow'` | TensorFlow is not installed in the active environment. | Install a TensorFlow runtime compatible with the source. The verified legacy path used TensorFlow 1.15.5 on Python 3.7. |
| `AttributeError: module 'tensorflow' has no attribute 'Session'` or `placeholder` | TensorFlow 2.x is installed and top-level TF1 APIs are not available. | Use a TF1-compatible environment, or port the code to `tf.compat.v1` with eager execution disabled. Do not treat a plain TF2 install as compatible with the original files. |
| Protobuf descriptor error mentioning `Descriptors cannot be created directly` | TensorFlow 1.15 with a too-new `protobuf` package. | Install `protobuf<3.20` in the environment used for the template. |
| `ModuleNotFoundError: No module named 'bunch'` | `utils.config` depends on the `bunch` package. | Install `bunch`, or replace it with `types.SimpleNamespace`, `argparse.Namespace`, or `munch` and update imports. |
| `ModuleNotFoundError: No module named 'tqdm'` | Example trainer imports `tqdm`. | Install `tqdm` or remove the progress-bar wrapper. |

## Config failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Example main prints `missing or invalid arguments` and exits with code `0` | The bare `except` in `mains/example.py` catches missing file, invalid JSON, missing dependency, or other errors. | Re-run with explicit `-c /path/to/config.json`; replace the bare `except` with explicit exception logging while debugging. |
| `FileNotFoundError` for config | `--config` is absent or path is relative to a different current directory than expected. | Use an absolute config path or run from the intended project directory. |
| `AttributeError: ... has no attribute 'state_size'` or another config key | JSON does not include a field read by model/trainer/base code. | Compare with [configuration](configuration.md) and add the missing key or change code to handle a default. |
| Outputs appear in an unexpected `../experiments` directory | `process_config` derives paths relative to the process current working directory. | Use absolute output paths, derive paths relative to the config file, or run from the expected `mains/`/project directory deliberately. |

## Tensor shapes and training-step failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Placeholder/feed shape error for `x` | Data batch feature shape does not match `[batch] + config.state_size`. | Align `state_size`, data generator output, and model placeholder. The example expects `[batch, 784]`. |
| Placeholder/feed shape error for `y` | Labels do not match the model's hard-coded `[batch, 10]` shape. | Add a `num_classes` config key and update both model output and labels, or one-hot encode labels to length 10. |
| `StopIteration` in `train_step` | A custom `next_batch` returns an exhausted iterator or a tuple instead of a generator. | Match the source contract `next(data.next_batch(batch_size))`, or update the trainer to consume the new data API. |
| Metrics logging fails with `'float' object has no attribute 'shape'` | `Logger.summarize` expects every summary value to expose `.shape`. | Pass NumPy scalars/arrays such as `np.asarray(loss)` or patch the logger to normalize values. |
| The template runs one more epoch than expected | `BaseTrain.train()` loops to `config.num_epochs + 1` starting from the current epoch tensor. | Change the range upper bound to `config.num_epochs`, or set `num_epochs` with the inclusive behavior in mind. |

## Checkpoint and summary failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Saver path errors or checkpoint files with unexpected names | `config.checkpoint_dir` is used both as a save prefix and as a latest-checkpoint directory. | Split directory and prefix, or update `save()` to use `os.path.join(config.checkpoint_dir, "model.ckpt")`. |
| `latest_checkpoint` never finds a saved checkpoint | The load path points to a filename prefix instead of the directory containing checkpoint state. | Pass the checkpoint directory to `tf.train.latest_checkpoint`, and save with a prefix inside that directory. |
| TensorBoard event files are missing | `summary_dir` parent was not created or logger construction failed. | Ensure summary directories exist before constructing `Logger`; check write permissions for the experiment workspace. |

## README/source mismatches

- The README describes Comet.ml reporting and an API key, but the inspected `utils/logger.py` writes TensorBoard summaries only. If Comet support is required, add explicit Comet dependency/import/client code and config handling; do not assume it exists.
- The README's folder names contain minor spelling/formatting inconsistencies (`model` vs `models`, `trainer` vs `trainers`, and spacing around `data_loader`). The checked source directories are `models/`, `trainers/`, and `data_loader/`.
- The repository name and README have historical spelling variants. Use the actual checkout layout for code paths.

## When to stop and redesign

Stop treating the original template as a drop-in runtime if:

- The project must use current TensorFlow 2.x/Keras idioms.
- Training must be distributed, mixed precision, or GPU-optimized.
- Data loading must use `tf.data`, streaming datasets, or large external storage.
- Experiment tracking must include Comet.ml, MLflow, W&B, or another service.

In those cases, use this skill to preserve the high-level separation of model/trainer/data/config/logger, but design a modern implementation instead of patching the legacy example line by line.
