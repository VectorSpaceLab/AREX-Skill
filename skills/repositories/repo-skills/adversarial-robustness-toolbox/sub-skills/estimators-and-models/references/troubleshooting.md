# Estimator Troubleshooting

Use this guide when wrapper construction, prediction, fitting, or gradient checks fail.

## Shape and channel-order errors

Symptoms:

- Prediction returns an unexpected shape.
- PyTorch convolution errors mention channel mismatch.
- TensorFlow/Keras errors mention incompatible input dimensions.
- Attacks generate arrays with the right batch size but the wrong image layout.

Fixes:

1. Confirm `input_shape` excludes the batch dimension.
2. For PyTorch image models, use NCHW data with `channels_first=True` unless the model was explicitly written for channels-last.
3. For TensorFlowV2/Keras image models, use NHWC data with `channels_first=False` unless the model was explicitly written for channels-first.
4. For tabular/tree/sklearn models, keep `input_shape=(num_features,)` and avoid image-style channel settings.
5. Run a tiny `predict` probe before constructing attacks.

## Label-format errors

Symptoms:

- Loss functions complain about target rank or target dtype.
- sklearn fit receives a two-dimensional target unexpectedly.
- TensorFlow sparse loss receives one-hot labels, or categorical loss receives class indices.

Fixes:

- ART classifier wrappers commonly accept one-hot labels and convert internally when the configured loss requires indices.
- `SklearnClassifier.fit` expects one-hot labels at the wrapper boundary and passes class indices to sklearn.
- PyTorch `CrossEntropyLoss`, `NLLLoss`, and `MultiMarginLoss` consume class indices after ART reduction.
- TensorFlow `SparseCategoricalCrossentropy` consumes class indices after ART reduction; `CategoricalCrossentropy` consumes one-hot labels.
- For direct framework training outside ART, use the label format required by the underlying framework or sklearn model.

## Missing `loss_gradient` or `class_gradient`

Symptoms:

- A white-box attack raises an estimator requirement error.
- `getattr(classifier, "loss_gradient", None)` is missing or not callable.
- PGD/FGSM/DeepFool/Carlini-style workflows fail on a black-box or tree wrapper.

Fixes:

1. Identify whether the estimator is gradient-enabled:
   - Usually yes: `PyTorchClassifier`, `TensorFlowV2Classifier`, `KerasClassifier`, `PyTorchRegressor`, `KerasRegressor`.
   - Sometimes: specialised sklearn wrappers such as logistic regression and SVC.
   - Usually no: `BlackBoxClassifier`, `BlackBoxRegressor`, `LightGBMClassifier`, raw boosted-tree boosters, and generic sklearn wrappers.
2. If gradients are absent, route to black-box or tree-specific attacks in `../evasion-and-preprocessing/SKILL.md`.
3. If metrics or certification need gradients, route to `../evaluation-and-certification/SKILL.md` and choose gradient-compatible metrics only.

## Black-box wrapper limitations

Symptoms:

- Calling `.fit()` on `BlackBoxClassifier` or `BlackBoxRegressor` raises `NotImplementedError`.
- A gradient attack refuses the estimator.
- Lookup-table predictions miss close floating-point inputs.

Fixes:

- Train the underlying model outside ART before wrapping it.
- Use attacks that are explicitly black-box or decision/query-based.
- For lookup tables, pass `(inputs, labels)` and only enable `fuzzy_float_compare=True` for small tables where approximate matching is required.
- Ensure the black-box prediction callable returns a full batch matrix, not a single row for the whole batch.

## PyTorch backend and fitting errors

Symptoms:

- CPU-only installation tries to use CUDA.
- `.fit()` raises an optimizer-required error.
- Loss function complains about label shape.
- Gradients return the wrong shape.

Fixes:

- Pass `device_type="cpu"` explicitly for CPU-only workflows.
- Supply an optimizer if `.fit()` will be called.
- Prefer model outputs as logits and pair them with a matching loss such as `torch.nn.CrossEntropyLoss()`.
- Use `input_shape` and `channels_first` that match the model's `forward` method.
- For a quick gradient check, call `loss_gradient(x_probe, y_probe)` and require `gradient.shape == x_probe.shape`.

## TensorFlowV2 and Keras fitting errors

Symptoms:

- `TensorFlowV2Classifier.fit` raises an error about missing `loss_object`, `optimizer`, or `train_step`.
- `loss_gradient` fails although `predict` works.
- Keras wrapper errors say the model is not compiled or not built.

Fixes:

- For TensorFlowV2 `.fit()`, supply either `train_step` or both `loss_object` and `optimizer`.
- For TensorFlowV2 gradients, supply `loss_object` even if no training is planned.
- For Keras, build and compile the model before wrapping if fitting through ART.
- Set `use_logits` truthfully: `True` for raw logits, `False` for softmax/probabilities.
- Keep `channels_first=False` for normal TensorFlow/Keras NHWC inputs.

## Boosted-tree wrapper errors

Symptoms:

- XGBoost wrapper rejects the model type.
- LightGBM `.fit()` raises `NotImplementedError`.
- Tree wrapper prediction shape is missing class columns.
- White-box neural attacks reject a tree estimator.

Fixes:

- Use `XGBoostClassifier` only with `xgboost.Booster` or `xgboost.XGBClassifier`.
- Use `LightGBMClassifier` only with an already trained `lightgbm.Booster`; train LightGBM before wrapping.
- Use `CatBoostARTClassifier` only with `catboost.core.CatBoostClassifier`.
- Provide `nb_features` or `nb_classes` when ART cannot infer them.
- Route tree verification and tree-specific metrics to `../evaluation-and-certification/SKILL.md`; route black-box evasion to `../evasion-and-preprocessing/SKILL.md`.

## `clip_values` and preprocessing mistakes

Symptoms:

- Attacks produce values outside the expected data range.
- Prediction works before wrapping but changes after wrapping.
- Gradients appear scaled unexpectedly.

Fixes:

- Set `clip_values` to the true model input bounds after any external preprocessing.
- Do not apply both external normalisation and ART `preprocessing` unless that is intentional.
- Remember ART `preprocessing=(a, b)` means `(x - a) / b`.
- If the model already includes normalisation layers or a sklearn pipeline, prefer `preprocessing=(0.0, 1.0)`.

## Optional dependency errors

Symptoms:

- Importing XGBoost, LightGBM, CatBoost, GPy, TensorFlow, Keras, or PyTorch wrappers raises `ImportError` or backend startup errors.

Fixes:

- Install only the backend needed by the chosen wrapper.
- For CPU-only PyTorch, still pass `device_type="cpu"` to ART's PyTorch wrappers.
- If the task is only model wrapping and prediction with sklearn/black-box, do not install deep-learning or boosted-tree extras.
- Route package installation and backend readiness checks to `../setup-and-backends/SKILL.md`.
