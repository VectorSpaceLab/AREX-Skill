# Tuning Troubleshooting

## Purpose

Use this for generic Keras tuning failures that are not specific to scikit-learn, image hypermodels, or distributed workers.

## Missing or wrong dependencies

### Bayesian optimization import or construction fails

**Symptoms**
- `Please install scipy before using the BayesianOptimization...`
- `Please install scikit-learn (sklearn) before using the BayesianOptimization...`

**Cause**
- The optional Bayesian extras are missing.

**Recovery**
- Install `keras-tuner[bayesian]` or the equivalent editable extra set.

### TensorFlow or Keras import fails

**Symptoms**
- The package import fails before any tuning code runs.

**Cause**
- The environment has `keras-tuner` but not a TensorFlow-backed Keras installation.

**Recovery**
- Install `keras-tuner[tensorflow-cpu]` for CPU use or `keras-tuner[tensorflow]` for a GPU-backed TensorFlow environment.

## TensorFlow-backed search missing TensorBoard

**Symptoms**
- A Keras search fails in `Tuner._configure_tensorboard_dir` with `ModuleNotFoundError: No module named 'tensorboard'`, even without a user TensorBoard callback.

**Recovery**
- Install `tensorboard` alongside the TensorFlow-backed KerasTuner environment, then recreate the tuner and retry the bounded search.

## Search-space failures

### Grid search ends too early

**Symptoms**
- You expected more trials than the tuner produced.

**Cause**
- The search space was not fully finite.

**Recovery**
- Use explicit `Choice` values or add `step=` to `Int` / `Float` ranges.

### Hyperband rejects `factor`

**Symptoms**
- `ValueError: factor needs to be a int larger than 1.`

**Recovery**
- Use `factor >= 2`.

### Conditional values are missing

**Symptoms**
- A hyperparameter does not show up in `hp.values`.

**Cause**
- It is inactive under the current conditional scope.

**Recovery**
- Check the parent hyperparameter value and the `conditional_scope()` block.

## Build and trial failures

### Model build does not return a Keras Model

**Symptoms**
- `FatalTypeError` about an invalid model instance.

**Recovery**
- Make sure `build(hp)` returns a compiled `keras.Model` when using the standard tuning loop.

### Trials retry more than expected

**Symptoms**
- A bad trial is retried several times.

**Cause**
- The code raised a generic exception instead of `FailedTrialError`.

**Recovery**
- Raise `FailedTrialError` for data- or configuration-specific failures you do not want retried.
- Raise `FatalError` only when the whole search should stop immediately.

### Saved models are missing

**Symptoms**
- `get_best_models()` cannot load a trial.

**Cause**
- The search directory is missing or not writable.

**Recovery**
- Re-run the tuner with a writable `directory`/`project_name` pair and repeat the search.

## Slow debug cycles

- Reduce the dataset to a synthetic fixture while validating the workflow.
- Reduce `max_trials` before running a larger project.
- Prefer `RandomSearch` while debugging the model-building function, then switch to the more expensive algorithm after the search space is stable.
