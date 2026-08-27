# DragonNet: TensorFlow and JAX

DragonNet estimates treatment effects with a shared representation, two outcome heads, a propensity head, and optional targeted regularization. In CausalML 0.17.0 it is available from:

```python
from causalml.inference.tf import DragonNet as TFDragonNet
from causalml.inference.jax import DragonNet as JAXDragonNet
```

Use DragonNet when treatment is binary and the unconfoundedness-style representation/propensity-head setup is appropriate. For hidden-confounder proxy modeling, use CEVAE instead.

## API facts

| Backend | Constructor-only differences | Core methods | Save/load |
| --- | --- | --- | --- |
| TensorFlow | no `seed` argument | `fit`, `predict`, `fit_predict`, `predict_tau`, `predict_propensity` | `save(h5_filepath)`, `load(h5_filepath, ratio=1.0, dragonnet_loss=...)` |
| JAX | adds `seed=0` | `fit`, `predict`, `fit_predict`, `predict_tau`, `predict_propensity` | `save(path)`, `load(path, input_dim=None)` |

Shared constructor defaults include `neurons_per_layer=200`, `targeted_reg=True`, `ratio=1.0`, `val_split=0.2`, `batch_size=64`, `epochs=100`, `learning_rate=1e-5`, `momentum=0.9`, `reg_l2=0.01`, `use_adam=True`, `adam_epochs=30`, `adam_learning_rate=1e-3`, and `verbose=True`.

Method signatures use the current neural-estimator order:

```python
model.fit(X, treatment, y, p=None)
model.predict(X, treatment=None, y=None, p=None)
model.fit_predict(X, treatment, y, p=None, return_components=False)
```

Prefer keyword arguments. `p` is accepted for API compatibility and is ignored.

## Outputs

After `fit`:

- `predict(X)` returns an array with shape `(n_samples, 4)` whose columns are `(y0, y1, propensity, epsilon)`.
- `predict_tau(X)` returns individual treatment effects as `(y1 - y0).reshape(-1, 1)`.
- `predict_propensity(X)` returns a 1-D propensity vector from column 2 of `predict(X)`.
- `fit_predict(...)` fits and returns `predict_tau(X)`. Do not rely on `return_components=True` to return all four components; call `predict(X)` explicitly when components are needed.

## Tiny CPU fit pattern

This is a wiring and shape check, not a quality benchmark.

```python
import numpy as np

rng = np.random.default_rng(7)
X = rng.normal(size=(100, 5)).astype("float32")
propensity = 1 / (1 + np.exp(-(X[:, 0] - 0.3 * X[:, 1])))
treatment = rng.binomial(1, propensity).astype("float32")
y = (0.5 + 1.2 * treatment + X[:, 0] + 0.1 * rng.normal(size=100)).astype("float32")
```

TensorFlow:

```python
from causalml.inference.tf import DragonNet

model = DragonNet(
    neurons_per_layer=16,
    targeted_reg=False,
    use_adam=True,
    adam_epochs=1,
    epochs=2,
    batch_size=32,
    val_split=0.2,
    verbose=False,
)
ite = model.fit_predict(X=X, treatment=treatment, y=y)
components = model.predict(X)
prop = model.predict_propensity(X)
assert ite.shape == (X.shape[0], 1)
assert components.shape == (X.shape[0], 4)
assert prop.shape == (X.shape[0],)
assert np.isfinite(ite).all()
```

JAX:

```python
from causalml.inference.jax import DragonNet

model = DragonNet(
    neurons_per_layer=16,
    targeted_reg=False,
    use_adam=True,
    adam_epochs=1,
    epochs=2,
    batch_size=32,
    val_split=0.2,
    verbose=False,
    seed=7,
)
model.fit(X=X, treatment=treatment, y=y)
ite = model.predict_tau(X)
components = model.predict(X)
prop = model.predict_propensity(X)
assert ite.shape == (X.shape[0], 1)
assert components.shape == (X.shape[0], 4)
assert prop.shape == (X.shape[0],)
assert np.isfinite(ite).all()
```

## Save and load

### TensorFlow DragonNet

The TensorFlow wrapper saves a Keras H5 file and its `load` method supplies the custom objects used by DragonNet.

```python
from pathlib import Path
from causalml.inference.tf import DragonNet

path = Path("dragonnet_tf.h5")
model = DragonNet(neurons_per_layer=16, targeted_reg=False, adam_epochs=1, epochs=2, verbose=False)
model.fit(X=X, treatment=treatment, y=y)
before = model.predict_tau(X)
model.save(path)

restored = DragonNet()
restored.load(path)
after = restored.predict_tau(X)
```

Keep the TensorFlow/Keras version compatible between save and load environments. If `targeted_reg=True` and a non-default loss is used, pass the same loss configuration to `load`.

### JAX DragonNet

The JAX wrapper saves an Orbax checkpoint directory. It writes model architecture metadata so `load(path)` can reconstruct the model; `input_dim` is only needed for old checkpoints that do not contain metadata.

```python
from pathlib import Path
from causalml.inference.jax import DragonNet

ckpt = Path("dragonnet_jax_ckpt")
model = DragonNet(neurons_per_layer=16, targeted_reg=False, adam_epochs=1, epochs=2, verbose=False, seed=7)
model.fit(X=X, treatment=treatment, y=y)
before = model.predict_tau(X)
model.save(ckpt)

restored = DragonNet(seed=7)
restored.load(ckpt)
after = restored.predict_tau(X)
```

Use a checkpoint directory path for JAX, not an H5 file. Keep the same JAX/Flax/Orbax generation for reliable restore.

## Interpreting DragonNet outputs

- `predict_tau(X)` is an ITE/CATE estimate. Aggregate with `ite.mean()` only after checking that treatment coding and outcome scale are meaningful.
- `predict_propensity(X)` should be finite and generally inside `(0, 1)`. Extreme values suggest overlap/common-support issues, which can destabilize targeted regularization.
- If you need AUUC, Qini, cumulative-gain, validation, or policy curves, pass the flattened ITE vector to the analysis-and-decision sub-skill after confirming model output shapes.
