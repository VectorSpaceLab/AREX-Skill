# Adversarial backends and training

Fairlearn adversarial mitigation fits a predictor network for the supervised target while training an adversary that tries to recover sensitive features from the predictor output. The predictor update penalizes information that helps the adversary.

## Constructor surface

Verified constructor surface for both `AdversarialFairnessClassifier` and `AdversarialFairnessRegressor`:

```text
AdversarialFairnessClassifier(
    *,
    backend="auto",
    predictor_model=None,
    adversary_model=None,
    predictor_optimizer="Adam",
    adversary_optimizer="Adam",
    constraints="demographic_parity",
    learning_rate=0.001,
    alpha=1.0,
    epochs=1,
    batch_size=32,
    shuffle=False,
    progress_updates=None,
    skip_validation=False,
    callbacks=None,
    cuda=None,
    warm_start=False,
    random_state=None,
)
```

Use `AdversarialFairnessRegressor` for continuous supervised targets with the same backend and training choices.

## Backend selection

| Backend | How to select | Verified in this skill? | Notes |
| --- | --- | --- | --- |
| PyTorch | `backend="torch"` with `torch.nn.Module` models or list builders | Yes, CPU and optional CUDA | Preferred validated path for this skill. |
| TensorFlow / Keras | `backend="tensorflow"` with `keras.Model` models or list builders | Documented only | Do not claim verification unless the environment is prepared and smoke-tested. |
| Auto | `backend="auto"` | Import-dependent | Useful for exploratory use, but explicit backend is better for reproducible reports. |

Do not mix backend objects. A PyTorch predictor with a Keras adversary is invalid.

## Model specification

Fairlearn accepts either backend-native model objects or a simple list builder.

List builder example:

```python
mitigator = AdversarialFairnessClassifier(
    backend="torch",
    predictor_model=[50, "leaky_relu"],
    adversary_model=[3, "leaky_relu"],
    epochs=5,
    batch_size=128,
    random_state=0,
)
```

The list contains hidden-layer widths, activation strings, or activation/layer callables. Fairlearn infers input/output sizes and appends the final activation for inferred binary/categorical outputs.

Explicit PyTorch model example:

```python
import torch
from fairlearn.adversarial import AdversarialFairnessClassifier

class Predictor(torch.nn.Module):
    def __init__(self, n_features: int):
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(n_features, 8),
            torch.nn.ReLU(),
            torch.nn.Linear(8, 1),
            torch.nn.Sigmoid(),
        )
    def forward(self, x):
        return self.layers(x)

class Adversary(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(1, 4),
            torch.nn.ReLU(),
            torch.nn.Linear(4, 1),
            torch.nn.Sigmoid(),
        )
    def forward(self, x):
        return self.layers(x)

mitigator = AdversarialFairnessClassifier(
    backend="torch",
    predictor_model=Predictor(X_train.shape[1]),
    adversary_model=Adversary(),
    learning_rate=0.01,
    epochs=3,
    batch_size=32,
    shuffle=True,
    random_state=0,
)
mitigator.fit(X_train, y_train, sensitive_features=A_train)
```

For the inspected PyTorch engine, binary losses use `torch.nn.BCELoss`; explicit custom binary modules should output values in `[0, 1]`.

## Data preparation

- `X` must be a 2D matrix of floats. Use sklearn preprocessing such as `ColumnTransformer`, `OneHotEncoder`, `SimpleImputer`, and `StandardScaler` before the adversarial estimator.
- Binary and categorical `y`/`sensitive_features` are transformed internally; continuous values are left continuous.
- For equalized odds, the adversary receives both predictor output and true label, so its input shape differs from demographic parity.
- All rows must be provided during the first `fit` call in this source.

Pipeline pattern with metadata routing:

```python
from sklearn.pipeline import make_pipeline
import sklearn

sklearn.set_config(enable_metadata_routing=True)
pipeline = make_pipeline(preprocessor, mitigator.set_fit_request(sensitive_features=True))
pipeline.fit(X_train_raw, y_train, sensitive_features=A_train)
sklearn.set_config(enable_metadata_routing=False)
```

## Callbacks and training controls

Use callbacks for validation, early stopping, or dynamic hyperparameters. A callback that returns `True` requests early stopping; returning a non-boolean value is an error.

```python
def callback(model, step, X_val, y_val, A_val):
    if step % 20 == 0:
        pred = model.predict(X_val)
        # compute and log assessment metrics here
    return False

mitigator = AdversarialFairnessClassifier(callbacks=callback, epochs=10, shuffle=True)
```

Training advice:

- Start with one hidden layer and a modest learning rate.
- Watch for mode collapse: almost all predictions become one class.
- Balance utility and disparity metrics; reducing adversary accuracy alone is not enough.
- Use `warm_start=True` only when deliberately continuing training on the same model setup.

## CUDA

Use CUDA only after verifying PyTorch can see it:

```python
import torch
print(torch.cuda.is_available())
```

Then pass a device string, for example:

```python
mitigator = AdversarialFairnessClassifier(..., backend="torch", cuda="cuda:0")
```

If CUDA is unavailable or mismatched, use CPU first and preserve CUDA as an optional acceleration path.

## Evaluation

After fitting:

```python
from fairlearn.metrics import MetricFrame, selection_rate
from sklearn.metrics import accuracy_score

pred = mitigator.predict(X_test)
mf = MetricFrame(
    metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
    y_true=y_test,
    y_pred=pred,
    sensitive_features=A_test,
)
print(mf.by_group)
print(mf.difference())
```

Compare against an unconstrained neural or sklearn baseline when the user asks whether adversarial mitigation helped.
