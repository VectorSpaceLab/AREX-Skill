# Framework integration troubleshooting

Use this reference to diagnose integration failures without accidentally turning an Aim logging task into a full framework installation or training run.

## Adapter import fails

Symptoms:

- `RuntimeError: This contrib module requires ... to be installed`
- `ModuleNotFoundError` for a framework package such as `paddle`, `mxnet`, `stable_baselines3`, `acme`, or `optuna`
- Callback import works in one environment but not in the training environment

Response:

1. Confirm the adapter the user actually needs.
2. Run a lightweight diagnostic:

   ```bash
   python scripts/aim_integration_snippets.py --check-optional
   ```

3. If the user approves importing optional frameworks, run:

   ```bash
   python scripts/aim_integration_snippets.py --check-optional --import-adapters
   ```

4. If the package is missing, choose either a targeted install for that single framework or direct `Run.track` fallback.
5. If the import fails inside a notebook after installation, restart the kernel and retry the import.

Do not report missing optional frameworks as a broken base Aim installation.

## Use direct fallback when a callback is too brittle

Direct `Run.track` is often the fastest repair when:

- The framework callback package is unavailable or version-incompatible.
- The user only needs a few metrics.
- The callback loses important context, step, epoch, or dataset split information.
- The metric is non-numeric, media-like, or an object that the adapter skips.
- The adapter uses a different constructor keyword than the user's example.

Minimal fallback:

```python
from aim import Run

run = Run(repo="path/to/aim-repo", experiment="manual_fallback")
run.track(loss_value, name="loss", step=global_step, epoch=epoch, context={"subset": "train"})
run.track(validation_loss, name="loss", epoch=epoch, context={"subset": "val"})
run.close()
```

For a framework logger that exposes the underlying Aim run as `experiment`, use that run for custom values:

```python
trainer.logger.experiment.track(value, name="custom_metric", step=step, context={"subset": "train"})
```

## Unexpected keyword argument

Some public examples use stale or inconsistent experiment keyword names. Prefer the current adapter signatures:

- Use `experiment` with Lightning, Hugging Face, Keras, TensorFlow Keras, Keras Tuner, XGBoost, CatBoost, LightGBM, Prophet, and PyTorch Ignite.
- Use `experiment_name` with Optuna, fastai, Paddle, MXNet, stable-baselines3, and ACME.

If the user sees `TypeError: __init__() got an unexpected keyword argument 'experiment_name'`, switch that adapter call to `experiment` if it is in the first group. If they see the inverse error, switch to `experiment_name` if it is in the second group. If the user's installed Aim version differs, inspect the installed signature before editing training code.

## Lightning-specific issues

- Import failure: install either `lightning` or `pytorch-lightning`; the adapter checks `lightning` first.
- Context parsing surprise: by default `train_`, `val_`, and `test_` prefixes become `subset` context values. Override `context_prefixes` or use direct tracking for custom layouts.
- `ValueError` about metric prefixes and context prefixes: do not combine deprecated `train_metric_prefix`, `val_metric_prefix`, or `test_metric_prefix` with custom `context_prefixes`.
- Distributed training: the logger writes only on rank zero. If metrics are missing, confirm the process emitting metrics is allowed to log.
- Resuming: use the adapter's `run_hash` only when the user intentionally wants to resume an existing Aim run.

## Hugging Face-specific issues

- The callback logs numeric values from `on_log`. Non-numeric values are skipped with a warning.
- `train_`, `eval_`, and `test_` prefixes become Aim `subset` contexts. Check metric names if the UI grouping looks wrong.
- Distributed training logs only on world process zero.
- To track generated text, sample images, confusion matrices, or dataset examples, use direct `callback.experiment.track(...)` and Aim object types from `tracking-sdk`.

## Keras and TensorFlow Keras issues

- Use `aim.keras.AimCallback` for standalone Keras and `aim.tensorflow.AimCallback` for `tf.keras`.
- The callback tracks epoch-end logs. If the user needs batch-level metrics, write a small custom Keras callback that calls `Run.track` in `on_train_batch_end`.
- `val_` keys are converted to validation context. If metric names are already custom, verify the resulting Aim names.
- Avoid relying on legacy `metrics(...)` compatibility helpers for new code; instantiate `AimCallback` directly with explicit `repo` and `experiment`.
- If a closed TensorFlow callback is reused and its run cannot be reopened cleanly, create a new callback instance rather than reusing the old one.

## Gradient boosting issues

- XGBoost and LightGBM adapters are callbacks; attach them through each library's callback list.
- CatBoost uses `log_cout=AimLogger(...)` and parses CatBoost text output. If CatBoost log formatting changes or values are missing, use direct tracking after evaluation or a custom callback.
- If the user needs data-split context, standard deviation handling, or exact boosting-iteration step semantics beyond the adapter output, direct `Run.track` from a custom callback is safer.

## Optuna issues

- For a single Aim run across trials, keep `as_multirun=False` and call `close()` after the study if more studies will run in the same process.
- For one Aim run per trial, set `as_multirun=True` and use `track_in_aim()` for additional objective-internal values.
- Use `n_jobs=1` when trial order must match Aim step order.
- Multi-objective studies require `metric_name` count to match returned objective values, unless using default name broadcasting.

## RL and logger-key issues

- stable-baselines3 integration expects scalar values and logger keys shaped like `tag/name`; keys without a slash may not map correctly. Use a custom output format or direct tracking if keys are different.
- ACME integration tracks logging payloads through `AimWriter`. If payloads are nested or unsupported, normalize them before passing to the writer.

## TensorBoard conversion fails

Symptoms and responses:

- `Could not process TensorBoard logs - failed to import tensorflow module.` Install/check TensorFlow in the conversion environment, or avoid conversion and use direct tracking for future runs.
- No event files found. Confirm the logdir points at the directory containing TensorBoard event files, not a parent with unrelated files or an empty training output directory.
- Unorganized event-file warnings. Point `--logdir` at a cleaner parent directory or try `--flat` if nested run grouping is intended.
- Unsupported plugin warnings. Scalars and images are the primary supported conversion targets; preserve original logs for custom conversion if other plugin types matter.
- Duplicate or stale imports. Understand the converter cache in the Aim repo and use `--no-cache` only when intentional reprocessing is desired.

Use the helper before executing conversion:

```bash
python scripts/tensorboard_sync_template.py --check-deps --logdir path/to/tensorboard-logdir --repo path/to/aim-repo
python scripts/tensorboard_sync_template.py --logdir path/to/tensorboard-logdir --repo path/to/aim-repo
```

Add `--execute` only after the printed command is correct.

## Side-effect boundaries

- Do not run expensive training examples to prove logging integration unless the user explicitly asks and provides runtime constraints.
- Do not install GPU-specific packages just for Aim logging. Aim can log CPU-side metrics from the user's code; accelerator setup belongs to the training framework.
- Do not run long-lived services while diagnosing framework callbacks. UI/server operation belongs to `cli-and-services`.
- Do not rely on current working directory for repository selection. Make `repo` explicit in snippets and commands.
