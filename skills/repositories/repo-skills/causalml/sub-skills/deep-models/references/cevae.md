# CEVAE: Torch/Pyro and JAX

CEVAE targets treatment-effect estimation with latent confounding. It assumes observed covariates are noisy proxies for an unobserved confounder and learns a latent-variable model for `z`, covariates `x`, treatment `t`, and outcome `y`.

In CausalML 0.17.0 it is available from:

```python
from causalml.inference.torch import CEVAE as TorchCEVAE
from causalml.inference.jax import CEVAE as JAXCEVAE
```

Use CEVAE when hidden-confounder proxy modeling is the reason to use a neural model. If the workflow is a propensity-head DragonNet treatment-effect estimator, use [`dragonnet.md`](dragonnet.md) instead.

## API facts

| Backend | Constructor differences | Core methods | Save/load |
| --- | --- | --- | --- |
| Torch/Pyro | no `seed` argument on the wrapper | `fit`, `predict`, `fit_predict` | no CausalML `save`/`load` wrapper |
| JAX | adds `seed=0` | `fit`, `predict`, `fit_predict` | `save(path)`, `load(path, feature_dim)` |

Shared constructor defaults include `outcome_dist="studentt"`, `latent_dim=20`, `hidden_dim=200`, `num_epochs=50`, `num_layers=3`, `batch_size=100`, `learning_rate=1e-3`, `learning_rate_decay=0.1`, `num_samples=1000`, and `weight_decay=1e-4`.

Supported `outcome_dist` values are `"bernoulli"`, `"exponential"`, `"laplace"`, `"normal"`, and `"studentt"`. Use `"normal"` for ordinary continuous smoke data.

Method signatures use the current neural-estimator order:

```python
model.fit(X, treatment, y, p=None)
model.predict(X, treatment=None, y=None, p=None)
model.fit_predict(X, treatment, y, p=None)
```

Prefer keyword arguments. `p` is accepted for API compatibility and is ignored.

## Data pattern for hidden-confounder CEVAE

CEVAE is designed for settings where `X` are proxies for a latent confounder, treatment is binary, and outcome is generated from both treatment and the latent factors. For a tiny wiring check:

```python
import numpy as np

rng = np.random.default_rng(11)
n = 120
z = rng.normal(size=n)
X = np.column_stack([
    z + 0.2 * rng.normal(size=n),
    -z + 0.2 * rng.normal(size=n),
    rng.normal(size=n),
]).astype("float32")
prob = 1 / (1 + np.exp(-z))
treatment = rng.binomial(1, prob).astype("float32")
y = (0.5 + 1.0 * treatment + z + 0.2 * rng.normal(size=n)).astype("float32")
```

## Torch/Pyro CEVAE recipe

```python
import numpy as np
import torch
from causalml.inference.torch import CEVAE

np.random.seed(11)
torch.manual_seed(11)

model = CEVAE(
    outcome_dist="normal",
    latent_dim=4,
    hidden_dim=16,
    num_layers=2,
    num_epochs=2,
    batch_size=32,
    learning_rate=1e-3,
    learning_rate_decay=0.1,
    num_samples=20,
)
ite = model.fit_predict(X=X, treatment=treatment, y=y)
ite = np.asarray(ite).reshape(-1)
assert ite.shape == (X.shape[0],)
assert np.isfinite(ite).all()
```

Important Torch/Pyro notes:

- Use `num_layers >= 2` for tiny CPU models. Smaller values can trigger Pyro internal indexing failures in reduced smoke configurations.
- `predict(X)` calls the Pyro CEVAE `ite` routine and returns treatment-effect estimates. Flatten the output before passing it to metric helpers.
- The CausalML Torch/Pyro wrapper exposes `fit`, `predict`, and `fit_predict`; it does not expose wrapper-level `save` or `load` methods.
- For reproducibility, seed both NumPy and Torch before constructing the model. The wrapper itself does not accept `seed`.

## JAX CEVAE recipe

```python
import numpy as np
from causalml.inference.jax import CEVAE

model = CEVAE(
    outcome_dist="normal",
    latent_dim=4,
    hidden_dim=16,
    num_layers=2,
    num_epochs=2,
    batch_size=32,
    learning_rate=1e-3,
    learning_rate_decay=0.1,
    num_samples=20,
    seed=11,
)
model.fit(X=X, treatment=treatment, y=y)
ite = model.predict(X)
ite = np.asarray(ite).reshape(-1)
assert ite.shape == (X.shape[0],)
assert np.isfinite(ite).all()
```

JAX CEVAE validates feature dimensionality at prediction time. If `X` has a different number of columns than the fit data, `predict` raises an error.

## JAX save and load

JAX CEVAE uses an Orbax checkpoint directory. Unlike JAX DragonNet, the CEVAE load method needs `feature_dim` and the restoring instance should be constructed with the same architecture and outcome settings used for training.

```python
from pathlib import Path
from causalml.inference.jax import CEVAE

ckpt = Path("cevae_jax_ckpt")
model = CEVAE(
    outcome_dist="normal",
    latent_dim=4,
    hidden_dim=16,
    num_layers=2,
    num_epochs=2,
    batch_size=32,
    num_samples=20,
    seed=11,
)
model.fit(X=X, treatment=treatment, y=y)
before = model.predict(X)
model.save(ckpt)

restored = CEVAE(
    outcome_dist="normal",
    latent_dim=4,
    hidden_dim=16,
    num_layers=2,
    batch_size=32,
    num_samples=20,
    seed=11,
)
restored.load(ckpt, feature_dim=X.shape[1])
after = restored.predict(X)
```

Use a fresh checkpoint directory and keep the JAX/Flax/Orbax generation compatible across save and load.

## Output handling

- Treat CEVAE output as an ITE vector and normalize it with `np.asarray(ite).reshape(-1)` before metrics.
- `num_samples` controls Monte Carlo effort in prediction; lower it for smoke checks, raise it for more stable estimates.
- `num_epochs`, `hidden_dim`, `latent_dim`, and `num_layers` drive runtime and capacity. Increase them only after a tiny shape check passes.
- For binary outcomes, select `outcome_dist="bernoulli"`; for continuous outcomes, start with `"normal"` or the default `"studentt"`.
