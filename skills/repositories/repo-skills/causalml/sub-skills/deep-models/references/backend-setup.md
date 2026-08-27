# Backend setup for CausalML deep models

CausalML's deep estimators live behind optional extras. Install only the backend you need, then run a tiny CPU import/shape check before launching a longer training job.

## Optional extras and imports

| Goal | Install extra | Runtime import |
| --- | --- | --- |
| TensorFlow DragonNet | `pip install "causalml[tf]"` | `from causalml.inference.tf import DragonNet` |
| Torch/Pyro CEVAE | `pip install "causalml[torch]"` | `from causalml.inference.torch import CEVAE` |
| JAX DragonNet or JAX CEVAE | `pip install "causalml[jax]"` | `from causalml.inference.jax import DragonNet, CEVAE` |

The package metadata for CausalML 0.17.0 declares these backend dependencies:

- `tf`: `tensorflow>=2.4.0`
- `torch`: `torch`, `pyro-ppl`
- `jax`: `jax>=0.4.1`, `flax>=0.11.0`, `optax>=0.1.4`, `orbax-checkpoint>=0.10.0`

The old `causalml.inference.nn` documentation target is stale for this version; import DragonNet from `causalml.inference.tf` or `causalml.inference.jax` instead.

## CPU-first backend checks

Use a backend-specific import check rather than importing every optional backend in a production process.

```bash
python - <<'PY'
from importlib.metadata import version
print("causalml", version("causalml"))
from causalml.inference.tf import DragonNet as TFDragonNet
print("tf DragonNet ok", TFDragonNet.__name__)
PY
```

```bash
python - <<'PY'
from importlib.metadata import version
print("causalml", version("causalml"))
from causalml.inference.torch import CEVAE as TorchCEVAE
print("torch CEVAE ok", TorchCEVAE.__name__)
PY
```

```bash
python - <<'PY'
from importlib.metadata import version
print("causalml", version("causalml"))
from causalml.inference.jax import DragonNet, CEVAE
print("jax models ok", DragonNet.__name__, CEVAE.__name__)
PY
```

## Data contract shared by these models

- `X`: dense numeric array-like feature matrix with shape `(n_samples, n_features)`. NumPy arrays and pandas DataFrames are accepted at wrapper boundaries.
- `treatment`: binary treatment indicator with shape `(n_samples,)`, coded as `0/1` or values coercible to numeric binary floats.
- `y`: numeric outcome vector with shape `(n_samples,)`.
- `p`: accepted in method signatures for compatibility but ignored by DragonNet and CEVAE wrappers.
- Use keyword calls: `model.fit(X=X, treatment=treatment, y=y)` and `model.fit_predict(X=X, treatment=treatment, y=y)`.

## Backend selection heuristics

- Choose TensorFlow DragonNet when a Keras/H5 workflow is already standard in the project and TensorFlow is available.
- Choose JAX DragonNet when you need the same DragonNet-style API with explicit `seed` support and Orbax checkpoint directories.
- Choose Torch/Pyro CEVAE when matching the Pyro reference CEVAE is more important than wrapper-level checkpointing.
- Choose JAX CEVAE when you need CEVAE with a JAX/Flax/Optax stack and wrapper-level `save(path)` / `load(path, feature_dim)`.

## CPU/GPU expectations

These wrappers can run on CPU for small smoke tests. Installing an extra does not guarantee an accelerator-enabled build:

- TensorFlow may print messages that CUDA drivers were not found; this is normal for CPU-only runs.
- Torch/Pyro uses whatever device the installed Torch/Pyro stack selects internally; the CausalML wrapper itself does not expose a device argument.
- JAX may fall back to CPU if no supported accelerator runtime is installed. For deterministic CPU smoke checks, set `JAX_PLATFORM_NAME=cpu` in the shell before running Python.
- GPU use depends on matching the backend's own accelerator wheels, drivers, and platform configuration. Validate the backend outside CausalML before expecting long neural runs to use GPU.

## Tiny smoke data pattern

Use a small synthetic numeric dataset to validate imports, fit/predict shape, and finite outputs. Keep epochs and Monte Carlo samples low; this checks wiring, not model quality.

```python
import numpy as np

rng = np.random.default_rng(7)
X = rng.normal(size=(80, 4)).astype("float32")
logit = X[:, 0] - 0.5 * X[:, 1]
prob = 1.0 / (1.0 + np.exp(-logit))
treatment = rng.binomial(1, prob).astype("float32")
y = (1.0 + 0.7 * treatment + X[:, 0] + 0.2 * rng.normal(size=80)).astype("float32")
```

Use the model-specific references for backend-specific tiny settings.
