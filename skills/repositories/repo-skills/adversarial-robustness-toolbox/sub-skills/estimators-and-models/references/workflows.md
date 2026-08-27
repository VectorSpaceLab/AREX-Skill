# Model Wrapping Workflows

Use these recipes to construct and validate ART estimators before sending them to attack, defence, metric, or certification workflows.

## Universal validation checklist

After constructing any estimator:

1. Prepare a tiny batch `x_probe` with the same dtype, rank, channel order, and feature range as production inputs.
2. Call `pred = estimator.predict(x_probe)`.
3. Assert `pred.shape[0] == x_probe.shape[0]` and, for classification, `pred.shape[1] == estimator.nb_classes`.
4. Assert `np.isfinite(pred).all()`.
5. If downstream code will call `.fit()`, run a one-batch or one-epoch dry run with tiny data and the same label format.
6. If downstream code needs gradients, call `loss_gradient` on a tiny batch and assert the returned shape equals `x_probe.shape`.
7. If any step fails, resolve it here before choosing an attack or metric.

## scikit-learn classifier recipe

Use this when the user has a sklearn classifier or pipeline.

```python
from art.estimators.classification import SklearnClassifier
from art.utils import to_categorical

# Train the sklearn model directly or through ART. ART fit expects one-hot labels.
classifier = SklearnClassifier(model=sklearn_model, clip_values=(0.0, 1.0))
classifier.fit(x_train, to_categorical(y_train, nb_classes=nb_classes))
pred = classifier.predict(x_probe)
```

Validation notes:

- `SklearnClassifier` is a factory. It returns a specialised ART wrapper for recognised sklearn classes and a generic wrapper otherwise.
- Generic prediction works if the sklearn model exposes `predict_proba` or `predict`.
- Use `use_logits=True` only when the model exposes `predict_log_proba`.
- Do not assume `loss_gradient` exists. If the downstream workflow needs gradients, probe for it and otherwise route to black-box or tree-specific attacks.

## black-box classifier recipe

Use this when the user has only a prediction function, hosted model, or fixed lookup table.

```python
from art.estimators.classification import BlackBoxClassifier

classifier = BlackBoxClassifier(
    predict_fn=predict_proba_batch,
    input_shape=(num_features,),
    nb_classes=nb_classes,
    clip_values=(0.0, 1.0),
)

pred = classifier.predict(x_probe)
assert pred.shape == (len(x_probe), nb_classes)
```

Validation notes:

- `predict_fn` receives a batch and must return one row per input.
- `.fit()` is intentionally unavailable; train the underlying model outside ART.
- `loss_gradient` is unavailable. If a user asks for PGD, FGSM, Carlini, DeepFool, or another white-box gradient attack on this wrapper, route to black-box attacks in `../evasion-and-preprocessing/SKILL.md`.
- Lookup tables can be passed as `(inputs, labels)`. Use `fuzzy_float_compare=True` only for small tables that need approximate float matching.

## PyTorch classifier recipe

Use this for `torch.nn.Module` classifiers.

```python
import torch
from art.estimators.classification import PyTorchClassifier

model = TorchModelReturningLogits()
loss = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

classifier = PyTorchClassifier(
    model=model,
    loss=loss,
    optimizer=optimizer,
    input_shape=(channels, height, width),
    nb_classes=nb_classes,
    clip_values=(0.0, 1.0),
    channels_first=True,
    device_type="cpu",  # keep explicit for CPU-only environments
)
```

Validation notes:

- Prefer logits from `forward`; ART attacks can work with probabilities, but logits often improve attack efficiency and numerical behaviour.
- For tabular data, use `input_shape=(num_features,)`.
- For NHWC tensors, either transpose to NCHW before the model or set `channels_first=False` only when the model truly expects channels-last tensors.
- `.fit()` needs an optimizer. Without it, prediction may work but training raises an optimizer error.
- `CrossEntropyLoss` expects class-index labels internally. ART accepts one-hot or index labels and reduces as needed.

## TensorFlowV2 classifier recipe

Use this for TensorFlow 2 callable models.

```python
import tensorflow as tf
from art.estimators.classification import TensorFlowV2Classifier

model = TFModelReturningLogitsOrProbabilities()
loss_object = tf.keras.losses.CategoricalCrossentropy(from_logits=True)
optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)

classifier = TensorFlowV2Classifier(
    model=model,
    nb_classes=nb_classes,
    input_shape=(height, width, channels),
    loss_object=loss_object,
    optimizer=optimizer,
    clip_values=(0.0, 1.0),
    channels_first=False,
)
```

Validation notes:

- `predict` can work with only a callable model.
- `.fit()` requires either a custom `train_step(model, images, labels)` or both `loss_object` and `optimizer`.
- `loss_gradient` requires a usable loss object. A prediction-only wrapper is not enough for white-box attack workflows.
- Use `SparseCategoricalCrossentropy` when the loss should consume class-index labels; ART will reduce one-hot labels.

## Keras classifier recipe

Use this for compiled Keras models, especially simple Sequential/Functional models.

```python
from art.estimators.classification import KerasClassifier

keras_model.compile(optimizer=optimizer, loss=loss, metrics=["accuracy"])
classifier = KerasClassifier(
    model=keras_model,
    use_logits=False,
    clip_values=(0.0, 1.0),
    channels_first=False,
)
```

Validation notes:

- The model must be built and compiled before fitting through ART.
- Set `use_logits=True` only if the model output layer returns logits. If the model ends with softmax, use `False`.
- For modern TensorFlow 2 custom training loops, prefer `TensorFlowV2Classifier`.

## boosted tree and GPy classifier recipes

### XGBoost

```python
from art.estimators.classification import XGBoostClassifier

classifier = XGBoostClassifier(
    model=xgb_model,
    clip_values=(0.0, 1.0),
    nb_features=num_features,
    nb_classes=nb_classes,
)
```

- `model` must be an `xgboost.Booster` or `xgboost.XGBClassifier`.
- `.fit()` is supported only for `XGBClassifier`.
- Treat it as black-box/tree-specific for attack routing; many white-box neural attacks are not compatible.

### LightGBM

```python
from art.estimators.classification import LightGBMClassifier
classifier = LightGBMClassifier(model=lightgbm_booster, clip_values=(0.0, 1.0))
```

- `model` must be an already trained `lightgbm.Booster`.
- `.fit()` is not implemented on the ART wrapper.

### CatBoost

```python
from art.estimators.classification import CatBoostARTClassifier
classifier = CatBoostARTClassifier(model=catboost_model, nb_features=num_features, clip_values=(0.0, 1.0))
```

- `model` must be a `catboost.core.CatBoostClassifier`.
- The wrapper predicts probabilities with `predict_proba`.

### GPy

```python
from art.estimators.classification import GPyGaussianProcessClassifier
classifier = GPyGaussianProcessClassifier(model=gpy_gpclassification_model, clip_values=(0.0, 1.0))
```

- `GPyGaussianProcessClassifier` is binary-only.
- `.fit()` is not implemented; train the GPy model first.
- `loss_gradient` and `class_gradient` are finite-difference approximations, so keep probes small.

## regression recipes

### sklearn regression

```python
from art.estimators.regression import ScikitlearnRegressor
regressor = ScikitlearnRegressor(model=sklearn_regressor, clip_values=(0.0, 1.0))
pred = regressor.predict(x_probe)
```

### PyTorch regression

```python
import torch
from art.estimators.regression import PyTorchRegressor

regressor = PyTorchRegressor(
    model=torch_model,
    loss=torch.nn.MSELoss(),
    optimizer=torch.optim.Adam(torch_model.parameters(), lr=1e-3),
    input_shape=(num_features,),
    clip_values=(0.0, 1.0),
    device_type="cpu",
)
```

### Keras regression

```python
from art.estimators.regression import KerasRegressor
keras_model.compile(optimizer="adam", loss="mse")
regressor = KerasRegressor(model=keras_model, clip_values=(0.0, 1.0))
```

### black-box regression

```python
from art.estimators.regression import BlackBoxRegressor
regressor = BlackBoxRegressor(
    predict_fn=predict_batch,
    input_shape=(num_features,),
    clip_values=(0.0, 1.0),
)
```

For regression, validate the output shape against the model target shape before using attacks or metrics. Prediction-only black-box regressors cannot support white-box input gradients; a supplied `loss_fn` is for loss-value workflows, not gradient-required attacks.

## Two required routing checks

### PGD requested on a black-box classifier

Do not try to make `ProjectedGradientDescent` work by passing a `BlackBoxClassifier`. PGD is a gradient attack. Route the task to black-box attacks such as HopSkipJump, Boundary, SimBA, Square, ZOO, or another compatible method through `../evasion-and-preprocessing/SKILL.md`.

### TensorFlowV2 `.fit()` requested without training objects

A `TensorFlowV2Classifier` can predict with only a model callable, but `.fit()` will fail unless one of these is true:

- `train_step` is supplied; or
- both `loss_object` and `optimizer` are supplied.

If the user only needs attacks with gradients, ensure `loss_object` is supplied even if no fitting is planned.
