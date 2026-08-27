# Troubleshooting search, parallelism, and result inspection

## 1. Main-guard and fork/forkserver issues

### Symptom

- The run hangs, repeats top-level code in subprocesses, or crashes when using `n_jobs > 1` or a user Dask client.
- A script that worked in a notebook fails when moved to a plain `.py` file.

### Cause

Parallel auto-sklearn uses `forkserver`-style process start behavior in parallel mode. That requires the caller's top-level code to be safe under repeated import/execution.

### Fix

- Put estimator construction and `fit()` inside `if __name__ == "__main__":`.
- Move dataset loading, temporary-directory setup, and any side-effectful top-level code into that guard or into helper functions.
- If the user supplies a Dask client, close it explicitly in `finally:` or equivalent cleanup code.

### Good guard pattern

```python
if __name__ == "__main__":
    X_train, X_test, y_train, y_test = ...
    automl = autosklearn.classification.AutoSklearnClassifier(n_jobs=4)
    automl.fit(X_train, y_train)
```

## 2. High memory use with `fork`

### Symptom

- Sequential runs appear to use much more memory than expected.
- Small datasets still trigger memory pressure.

### Cause

In single-core local mode, Python can use `fork`, which copies the parent's address space. Large imported objects in the main process inflate the apparent child-process memory footprint.

### Fix

- Prefer a guarded parallel run or a user Dask client when you want `forkserver` rather than plain `fork`.
- Avoid loading huge datasets or large arrays at module import time.
- Keep large cached objects out of the parent process before the model-evaluation subprocess starts.
- Reduce `memory_limit` only if the problem is really model size rather than parent-process copy overhead.

## 3. Shared filesystem required for workers

### Symptom

- Dask workers fail to find training data, model files, or predictions.
- Ensemble building cannot load artifacts from remote workers.

### Cause

All workers must see the same file system location for auto-sklearn's temporary run directories and model artifacts.

### Fix

- Use a shared filesystem path for `tmp_folder` and any persistent output directory.
- Confirm all worker nodes can read and write that path.
- If workers do not share a filesystem, do not expect multi-machine parallelism to work correctly.

## 4. Memory limit too small

### Symptom

- Many `Memout` runs.
- Ensemble building or model search stops after very few successful evaluations.
- The run log says a model or ensemble process exceeded memory.

### Cause

`memory_limit` is per job. In parallel search, total use can multiply by `n_jobs`.

### Fix

- Increase `memory_limit` for the chosen model family.
- Reduce `n_jobs` if the machine cannot support the aggregate memory.
- Remove oversized preprocessing or overly broad include lists.
- For CV/custom split workflows, make sure compression/subsampling choices are not masking the true data footprint.

## 5. Time limit too small

### Symptom

- Very few successful runs.
- The optimizer reports timeouts or never reaches meaningful ensemble size.
- `sprint_statistics()` shows poor run coverage.

### Cause

The total time budget may be too tight for both search and ensemble construction, or `per_run_time_limit` is too aggressive.

### Fix

- Raise `time_left_for_this_task`.
- Use a smaller `per_run_time_limit` only if you still want multiple candidate runs.
- Remember that auto-sklearn may cap per-run time so at least two models can be trained.
- If you want a quick dry run, reduce the search space with `include` rather than starving the optimizer.

## 6. `disable_evaluator_output` conflicts

### Symptom

- `predict()` raises `NotImplementedError`.
- Ensemble loading or inspection is missing expected artifacts.
- The run appears to succeed but cannot produce predictions.

### Cause

`disable_evaluator_output=True` disables model and prediction output. Without those artifacts, auto-sklearn cannot reconstruct the normal prediction path.

### Fix

- Leave `disable_evaluator_output=False` if you need `predict()`, `show_models()`, or ensemble inspection.
- If you only need optimizer metadata, use a selective list and avoid disabling `model` or `y_optimization` unless you truly do not need them.
- For post-hoc `fit_ensemble()`, keep the outputs needed by the ensemble builder.

## 7. Disk growth and cleanup

### Symptom

- Temporary directories grow rapidly.
- The run fills the disk with model artifacts or test predictions.
- Old temporary data remains after the fit.

### Cause

- `tmp_folder` is persistent.
- `delete_tmp_folder_after_terminate=False` retains all runtime artifacts.
- `max_models_on_disc` allows many models and predictions to stay on disk.
- Ensemble building can briefly exceed the configured limit because it may create new artifacts before deleting old ones.

### Fix

- Use a dedicated run directory.
- Leave `delete_tmp_folder_after_terminate=True` unless you need inspection.
- Lower `max_models_on_disc` to trim the retained run set.
- If you also pass a test set, remember that test predictions consume extra space.
- Clean user-created temp directories after inspection.

## 8. Thread oversubscription

### Symptom

- CPU usage is much higher than expected.
- Parallel search slows down instead of speeding up.
- BLAS/OpenMP-heavy models thrash on a many-core machine.

### Cause

Scientific libraries may spawn their own worker threads, multiplying with auto-sklearn job-level parallelism.

### Fix

Set before starting Python:

```bash
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

Also keep `threads_per_worker=1` for Dask workers unless you have a specific reason not to.

## 9. Dask worker cleanup

### Symptom

- Workers remain alive after the run.
- A reused notebook/kernel accumulates stale clusters.
- `LocalDask` appears to keep old clients around.

### Cause

- A user-owned Dask client was not closed.
- A custom script did not close the cluster or worker processes.
- The run was interrupted before cleanup.

### Fix

- Treat `UserDask` as user-owned: close the `Client` and cluster yourself.
- Use context managers when possible.
- For `LocalDask`, prefer `with LocalDask(...) as client:` so cleanup happens automatically.
- After an interrupted run, explicitly shut down stale scheduler/worker processes before restarting.

## 10. Result inspection surprises

### Symptom

- `leaderboard()` or `show_models()` returns fewer rows than expected.
- `cv_results_` is missing data.
- `performance_over_time_` lacks ensemble columns.

### Cause

- `ensemble_only=True` hides non-ensemble runs.
- Partial-CV modes do not support `cv_results_`.
- No ensemble exists because `ensemble_class=None` or because output retention was disabled.

### Fix

- Use `leaderboard(ensemble_only=False)` to inspect all evaluated runs.
- Use `ensemble_class` settings that actually build an ensemble.
- Check whether `disable_evaluator_output` removed required artifacts.
- When in doubt, start with `sprint_statistics()` and then inspect `show_models()`.
