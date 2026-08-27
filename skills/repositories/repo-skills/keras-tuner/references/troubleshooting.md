# Troubleshooting

## Purpose

Use this for predictable install/import, optional dependency, and search failures that cross multiple KerasTuner workflows.

## Install and import failures

### `ImportError` when importing the package

**Symptoms**
- `ImportError` for `tensorflow`, `keras`, or `keras_tuner` itself.

**Likely cause**
- The environment has the package installed without TensorFlow support.

**Fix**
- Install the CPU TensorFlow extra for a normal workflow:

```bash
python -m pip install "keras-tuner[tensorflow-cpu]"
```

- If you need Bayesian optimization or scikit-learn tuning, add the `bayesian` extra:

```bash
python -m pip install "keras-tuner[tensorflow-cpu,bayesian]"
```

### Wrong backend import

**Symptoms**
- Code tries `from keras_tuner.backend import backend` and fails.

**Likely cause**
- `backend` is a module here; the callable is `keras_tuner.backend.config.backend()`.

**Fix**

```python
from keras_tuner.backend import config
print(config.backend())
```

## Optional dependency failures

### Bayesian optimization missing SciPy or scikit-learn

**Symptoms**
- `ImportError: Please install scipy...`
- `ImportError: Please install scikit-learn...`

**Fix**
- Install the `bayesian` extra.
- Recreate the tuner after the dependency is installed; the constructor performs the check.

### TensorFlow-backed search missing TensorBoard

**Symptoms**
- A Keras search fails in `Tuner._configure_tensorboard_dir` with `ModuleNotFoundError: No module named 'tensorboard'`, even though no explicit TensorBoard callback was supplied.

**Cause**
- This KerasTuner 1.4.8 TensorFlow execution path imports the TensorBoard HParams API while preparing each trial.

**Fix**
- Install TensorBoard in the same environment as TensorFlow and KerasTuner:

```bash
python -m pip install tensorboard
```

### Sklearn tuning missing scikit-learn

**Symptoms**
- `ImportError: Please install sklearn before using the SklearnTuner.`

**Fix**
- Install `scikit-learn` or the `bayesian` extra.
- If you want DataFrame inputs, also install `pandas`.

### DataFrame inputs fail

**Symptoms**
- `Expected the data to be numpy.ndarray or pandas.DataFrame.`

**Fix**
- Pass `numpy.ndarray` or `pandas.DataFrame` only.
- Install `pandas` if you want DataFrame support.

## Search-space and objective failures

### `Hyperband` rejects the factor

**Symptoms**
- `ValueError: factor needs to be a int larger than 1.`

**Fix**
- Use `factor >= 2`.

### `Tuner._try_build` rejects the model

**Symptoms**
- A `FatalTypeError` says the build function did not return a valid Keras Model.

**Fix**
- Make `build(hp)` return a compiled `keras.Model` when using a standard tuner.
- If you are tuning a black-box function, subclass `Tuner` and override `run_trial` instead.

### Trial failures and retries

**Symptoms**
- A trial is marked `FAILED` or `INVALID`.
- The search retries more times than expected.

**Fix**
- `FailedTrialError` stops retrying that trial.
- Other exceptions are retried up to `max_retries_per_trial`.
- `FatalError` propagates immediately and should stop the search.

### Grid search appears incomplete

**Symptoms**
- The search stops before covering every value you expected.

**Likely cause**
- The space is not fully finite.

**Fix**
- Use only finite `Choice` spaces when you need exhaustive coverage.
- Add explicit `step` values for integer and float grids.

## Image hypermodel failures

### Missing `classes` or input shape

**Symptoms**
- `You must specify classes when include_top=True`
- `You must specify either input_shape or input_tensor`

**Fix**
- Pass the required constructor arguments.

### HyperImageAugment parameter validation

**Symptoms**
- `must be int`
- `must be int or float`
- `exceed 2`

**Fix**
- Keep `augment_layers` numeric.
- Use one numeric value or a two-element range for transform factors.

### EfficientNet first-run download

**Symptoms**
- First build is slow or fails when offline.

**Likely cause**
- `HyperEfficientNet` delegates to Keras Applications EfficientNet backbones, which can fetch pretrained weights on first use.

**Fix**
- Allow the weight download once, or pre-cache the Keras Applications weights in an online environment before using this workflow offline.

## Distributed-tuning failures

See `sub-skills/distributed-tuning/references/troubleshooting.md` for `KERASTUNER_*` environment variable issues, chief/worker coordination, and port/timeouts.
