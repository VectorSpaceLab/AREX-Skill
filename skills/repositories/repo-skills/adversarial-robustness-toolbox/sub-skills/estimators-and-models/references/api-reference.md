# ART Estimator API Reference

This reference covers the selected model-wrapper scope for ART 1.20.x. Use it to choose an estimator, check constructor arguments, and decide whether a downstream ART workflow can ask for gradients or training.

## Estimator choice table

| User model or access pattern | Use ART wrapper | Prediction contract | Fit contract | Gradient contract | Key notes |
|---|---|---|---|---|---|
| scikit-learn classifier with `predict_proba` or `predict` | `art.estimators.classification.SklearnClassifier` | `predict(x)` returns `(n, nb_classes)` probabilities or one-hot classes | `fit(x, y)` expects one-hot labels and forwards to sklearn with index labels | Generic wrapper has no `loss_gradient`; selected specialised sklearn wrappers provide gradients, notably logistic regression and SVC | Convenience factory returns specialised wrappers when ART recognises the sklearn class. Use `use_logits=True` only if the model exposes `predict_log_proba`. |
| PyTorch `torch.nn.Module` classifier | `PyTorchClassifier` | Model should return logits/probabilities with class dimension; logits are preferred | Needs `optimizer` for `.fit()`; accepts index or one-hot labels and converts as needed for the loss | Gradient-enabled; supports `loss_gradient` and `class_gradient` | Default `device_type='gpu'`; pass `device_type='cpu'` for CPU-only use. Default image layout is `channels_first=True`. |
| TensorFlow 2 callable/Keras-style model | `TensorFlowV2Classifier` | Callable must accept `model(x, training=...)` and return class outputs | `.fit()` requires either `train_step` or both `loss_object` and `optimizer` | Gradient-enabled when `loss_object` is available for loss gradients | Default image layout is `channels_first=False`. Sparse categorical loss reduces one-hot labels to index labels. |
| Keras compiled model | `KerasClassifier` | Compiled Keras model returns probabilities or logits | Uses compiled model `.fit()`; labels may be one-hot or index | Gradient-enabled through Keras/TensorFlow graph | Set `use_logits` truthfully. Prefer TensorFlowV2Classifier for new TF2 eager workflows that need custom train steps. |
| Prediction callable or lookup table for classification | `BlackBoxClassifier` | `predict_fn(x_batch)` must return `(batch, nb_classes)` scores/probabilities; lookup table is `(inputs, labels)` | Not implemented | No white-box gradients | Use only black-box attacks/metrics. `fuzzy_float_compare=True` helps lookup-table float matching but can be slow. |
| XGBoost model | `XGBoostClassifier` | `xgboost.Booster` uses `DMatrix`; `XGBClassifier` uses `predict_proba` | `.fit()` only for `XGBClassifier`, not raw `Booster` | Not a white-box neural-gradient wrapper | Provide `nb_features` and `nb_classes` when ART cannot infer them. Tree verification/metrics route to evaluation. |
| LightGBM `Booster` | `LightGBMClassifier` | Uses booster `.predict()` | Not implemented | Not a white-box neural-gradient wrapper | Requires an already trained `lightgbm.Booster`; input shape is inferred from `num_feature()`. |
| CatBoost classifier | `CatBoostARTClassifier` | Uses `predict_proba` | Forwards `.fit()` to CatBoost with preprocessed labels | Not a white-box neural-gradient wrapper | Provide `nb_features` when ART cannot infer input shape. |
| GPy Gaussian process classifier | `GPyGaussianProcessClassifier` | Binary probabilities `(n, 2)` | Not implemented | Provides finite-difference `class_gradient` and `loss_gradient` | Binary-only wrapper around `GPy.models.GPClassification`; gradients are approximate and can be slower than framework autodiff. |
| scikit-learn regressor | `art.estimators.regression.ScikitlearnRegressor` | `predict(x)` returns regression outputs | `fit(x, y)` forwards to sklearn | Generic regressor has no `loss_gradient`; decision-tree regressor exposes tree structure for relevant workflows | Use regression attacks/metrics that accept ART regressors. |
| PyTorch regressor | `PyTorchRegressor` | Model returns regression output tensor | Needs `optimizer` for `.fit()` | Gradient-enabled; supports `loss_gradient` | Pass `device_type='cpu'` for CPU-only use. |
| Keras regressor | `KerasRegressor` | Compiled Keras model returns regression output | Uses compiled model `.fit()` | Gradient-enabled | Keep target shape consistent with the model output. |
| Regression prediction callable or lookup table | `BlackBoxRegressor` | `predict_fn(x_batch)` or lookup table returns regression values | Not implemented | No white-box gradients; optional `loss_fn` supports loss-value workflows, not input gradients | Use black-box-compatible regression workflows only. |

## Verified constructor signatures

The selected wrapper signatures are:

```python
PyTorchClassifier(
    model, loss, input_shape, nb_classes, optimizer=None,
    use_amp=False, opt_level='O1', loss_scale='dynamic',
    channels_first=True, clip_values=None,
    preprocessing_defences=None, postprocessing_defences=None,
    preprocessing=(0.0, 1.0), device_type='gpu'
)

TensorFlowV2Classifier(
    model, nb_classes, input_shape, loss_object=None,
    optimizer=None, train_step=None, channels_first=False,
    clip_values=None, preprocessing_defences=None,
    postprocessing_defences=None, preprocessing=(0.0, 1.0)
)

KerasClassifier(
    model, use_logits=False, channels_first=False, clip_values=None,
    preprocessing_defences=None, postprocessing_defences=None,
    preprocessing=(0.0, 1.0), input_layer=0, output_layer=0
)

SklearnClassifier(
    model, clip_values=None, preprocessing_defences=None,
    postprocessing_defences=None, preprocessing=(0.0, 1.0), use_logits=False
)

BlackBoxClassifier(
    predict_fn, input_shape, nb_classes, clip_values=None,
    preprocessing_defences=None, postprocessing_defences=None,
    preprocessing=(0.0, 1.0), fuzzy_float_compare=False
)

XGBoostClassifier(
    model=None, clip_values=None, preprocessing_defences=None,
    postprocessing_defences=None, preprocessing=(0.0, 1.0),
    nb_features=None, nb_classes=None
)

LightGBMClassifier(
    model=None, clip_values=None, preprocessing_defences=None,
    postprocessing_defences=None, preprocessing=(0.0, 1.0)
)

CatBoostARTClassifier(
    model=None, preprocessing_defences=None, postprocessing_defences=None,
    preprocessing=(0.0, 1.0), clip_values=None, nb_features=None
)

GPyGaussianProcessClassifier(
    model=None, clip_values=None, preprocessing_defences=None,
    postprocessing_defences=None, preprocessing=(0.0, 1.0)
)

ScikitlearnRegressor(
    model, clip_values=None, preprocessing_defences=None,
    postprocessing_defences=None, preprocessing=(0.0, 1.0)
)

PyTorchRegressor(
    model, loss, input_shape, optimizer=None,
    use_amp=False, opt_level='O1', loss_scale='dynamic',
    channels_first=True, clip_values=None,
    preprocessing_defences=None, postprocessing_defences=None,
    preprocessing=(0.0, 1.0), device_type='gpu'
)

KerasRegressor(
    model, channels_first=False, clip_values=None,
    preprocessing_defences=None, postprocessing_defences=None,
    preprocessing=(0.0, 1.0), input_layer=0, output_layer=0
)

BlackBoxRegressor(
    predict_fn, input_shape, loss_fn=None, clip_values=None,
    preprocessing_defences=None, postprocessing_defences=None,
    preprocessing=(0.0, 1.0), fuzzy_float_compare=False
)
```

## Cross-cutting estimator contracts

### `input_shape`

`input_shape` is the shape of one sample, excluding the batch dimension.

- Tabular examples: `(4,)`, `(784,)`.
- PyTorch image examples commonly use `(channels, height, width)` with `channels_first=True`.
- TensorFlow/Keras image examples commonly use `(height, width, channels)` with `channels_first=False`.
- Boosted tree wrappers use flat feature vectors; provide `nb_features` when model metadata cannot supply it.

### `nb_classes`

`nb_classes` is required by neural and black-box classifiers and may be inferred for some sklearn/tree wrappers. It must match the second dimension returned by `predict(x)`.

- Classification predictions should have shape `(n_samples, nb_classes)`.
- Binary GPy classification is fixed to two output columns.
- A single-output Keras binary classifier is represented as two ART classes internally.

### Labels

ART classification wrappers generally accept one-hot labels at the public wrapper level. Several framework losses convert labels internally:

- `PyTorchClassifier` with `CrossEntropyLoss`, `NLLLoss`, or `MultiMarginLoss` reduces one-hot labels to integer class indices for the loss.
- `TensorFlowV2Classifier` with `SparseCategoricalCrossentropy` reduces one-hot labels to integer class indices.
- `SklearnClassifier.fit` accepts one-hot labels and passes index labels to sklearn.
- For black-box prediction-only wrappers, `.fit()` is not available; train the underlying model before wrapping.

### `clip_values`

`clip_values=(min, max)` tells ART the legal feature range. It is important for attacks and preprocessing checks, even if prediction works without it.

- Use scalars when every feature shares the same range, for example `(0.0, 1.0)`.
- Use arrays when every feature has its own bounds; each array must be broadcast-compatible with one sample.
- `min` must be strictly smaller than `max` for every feature.

### `preprocessing`

`preprocessing=(subtrahend, divisor)` applies standardisation as `(x - subtrahend) / divisor` before the model sees data. The same operation participates in gradient backpropagation for gradient-enabled estimators.

Do not double-normalise: if the original model already includes normalisation layers or a sklearn pipeline, set ART `preprocessing=(0.0, 1.0)` unless you deliberately want ART to own that transform.

### Gradient-enabled versus black-box

Gradient-required attacks and metrics need an estimator with `loss_gradient` or `class_gradient`. Before routing to a white-box workflow, check:

```python
has_loss_gradient = callable(getattr(classifier, "loss_gradient", None))
has_class_gradient = callable(getattr(classifier, "class_gradient", None))
```

- `PyTorchClassifier`, `TensorFlowV2Classifier`, `KerasClassifier`, `PyTorchRegressor`, and `KerasRegressor` are gradient-enabled when their loss/training objects are configured.
- Some specialised sklearn wrappers provide gradients; the generic sklearn classifier does not.
- `BlackBoxClassifier`, `BlackBoxRegressor`, `LightGBMClassifier`, raw `XGBoostClassifier` booster wrappers, and most tree wrappers should be treated as black-box or tree-specific, not white-box neural-gradient estimators.
