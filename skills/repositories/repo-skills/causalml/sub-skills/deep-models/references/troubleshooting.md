# Troubleshooting deep-model workflows

## Import errors

### `ModuleNotFoundError` for TensorFlow, Torch, Pyro, JAX, Flax, Optax, or Orbax

Install the matching optional extra for the model being used:

```bash
pip install "causalml[tf]"      # TensorFlow DragonNet
pip install "causalml[torch]"   # Torch/Pyro CEVAE
pip install "causalml[jax]"     # JAX DragonNet and JAX CEVAE
```

Do not assume one optional backend installs the others.

### `causalml.inference.nn` cannot be imported

Use the current deep-model modules instead:

```python
from causalml.inference.tf import DragonNet
from causalml.inference.torch import CEVAE
from causalml.inference.jax import DragonNet, CEVAE
```

`causalml.inference.nn` is a stale documentation target for this version.

## CUDA and accelerator messages

- TensorFlow may print that CUDA drivers were not found; this is expected in CPU-only environments and does not by itself mean a CPU smoke test failed.
- JAX may select CPU when no supported accelerator runtime is present. To force CPU for a smoke check, set `JAX_PLATFORM_NAME=cpu` before starting Python.
- The CausalML wrappers do not add accelerator configuration arguments. Validate TensorFlow, Torch, or JAX accelerator availability at the backend level before expecting long runs to use GPU.
- If Torch/Pyro and JAX conflict over threading or OpenMP in one process, run backend comparisons in separate Python processes. For local experiments, constraining `OMP_NUM_THREADS=1` can reduce thread-runtime conflicts.

## Shape and dtype errors

Symptoms:

- `ValueError` about feature dimensions.
- Tensor conversion failures.
- Non-finite losses or predictions.
- Metric functions later reject ITE arrays.

Checks:

```python
import numpy as np

X = np.asarray(X, dtype="float32")
treatment = np.asarray(treatment, dtype="float32").reshape(-1)
y = np.asarray(y, dtype="float32").reshape(-1)
assert X.ndim == 2
assert treatment.shape == (X.shape[0],)
assert y.shape == (X.shape[0],)
assert set(np.unique(treatment)).issubset({0.0, 1.0})
```

Then call with keywords:

```python
model.fit(X=X, treatment=treatment, y=y)
```

For CEVAE outputs, flatten before scoring:

```python
ite = np.asarray(model.predict(X)).reshape(-1)
```

For DragonNet, use `predict_tau(X)` for ITE and `predict(X)` only when you need all four components `(y0, y1, propensity, epsilon)`.

## Argument-order warnings

Neural estimator methods currently accept `X, treatment, y, p`, while migration warnings point toward a future `X, y, treatment, p` order. Avoid positional ambiguity by always writing:

```python
model.fit(X=X, treatment=treatment, y=y)
ite = model.fit_predict(X=X, treatment=treatment, y=y)
```

## Pyro CEVAE `num_layers` failures

Tiny Torch/Pyro CEVAE configurations can fail internally when `num_layers` is too small. Use at least two layers even for a smoke test:

```python
from causalml.inference.torch import CEVAE
model = CEVAE(outcome_dist="normal", latent_dim=4, hidden_dim=16, num_layers=2, num_epochs=2)
```

If runtime remains high, reduce `num_epochs`, `hidden_dim`, `latent_dim`, and `num_samples`; do not reduce `num_layers` below 2 for the tiny check.

## Slow training

Deep causal estimators are much slower than classical meta-learners. For smoke checks:

- DragonNet: use `neurons_per_layer=16`, `targeted_reg=False`, `adam_epochs=1`, `epochs=2`, `batch_size=32`, `verbose=False`.
- CEVAE: use `latent_dim=4`, `hidden_dim=16`, `num_layers=2`, `num_epochs=2`, `batch_size=32`, `num_samples=20`.
- Keep data small, but large enough for validation splits and both treatment classes.
- Increase capacity and epochs only after import, fit, and predict shapes are confirmed.

## Treatment class and overlap problems

DragonNet and CEVAE expect binary treatment. If a tiny sample accidentally contains only one treatment class, training or propensity behavior may be poor. Regenerate data or stratify the sample so both `0` and `1` are present.

For DragonNet, inspect propensity output:

```python
prop = model.predict_propensity(X)
assert np.isfinite(prop).all()
print(prop.min(), prop.max())
```

Values extremely close to 0 or 1 indicate weak overlap; consider a larger sample, better feature preprocessing, or a non-neural estimator better suited to the data volume.

## Save/load failures

### TensorFlow DragonNet

- Use `model.save("name.h5")` and `restored.load("name.h5")`.
- Keep TensorFlow/Keras versions compatible across save and load.
- If custom targeted-regularization losses were changed, pass compatible loss configuration to `load`.

### JAX DragonNet

- Use a checkpoint directory path, not an H5 file.
- `save(path)` writes model metadata; `load(path)` normally reconstructs the model without `input_dim`.
- If loading an older checkpoint without metadata, provide `input_dim`.

### JAX CEVAE

- Use a checkpoint directory path.
- Recreate the restoring `CEVAE` instance with the same `outcome_dist`, `latent_dim`, `hidden_dim`, and `num_layers` as training.
- Call `load(path, feature_dim=X.shape[1])` before `predict`.
- Use a fresh or intentionally managed checkpoint directory to avoid stale Orbax contents.

### Torch/Pyro CEVAE

The CausalML wrapper exposes no `save` or `load` methods. If a workflow needs a persistent model artifact, prefer JAX CEVAE or document a project-specific Pyro serialization approach outside the CausalML wrapper.

## Non-finite training or unstable predictions

- Standardize or scale high-magnitude continuous features.
- Confirm `y` matches the selected CEVAE `outcome_dist`.
- Reduce learning rate if losses diverge.
- For DragonNet, try `targeted_reg=False` for debugging, then re-enable targeted regularization for the intended estimator.
- For CEVAE, reduce `num_samples` only for speed; increase it again when estimates look too noisy.
