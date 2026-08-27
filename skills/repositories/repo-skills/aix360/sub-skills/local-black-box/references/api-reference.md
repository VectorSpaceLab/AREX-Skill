# Local black-box API reference

The wrapper classes preserve the underlying LIME or SHAP object in
`wrapper.explainer`. Their `set_params` methods are placeholders in this
release; pass constructor/explanation options to the underlying APIs instead.
The signatures below are the inspected AIX360 0.3.0 and LIME contracts. SHAP
itself is version-sensitive, so inspect the installed SHAP version before
relying on a newer return layout.

## LIME wrappers

Import from `aix360.algorithms.lime`:

| Wrapper constructor | AIX360 method | Input and output |
|---|---|---|
| `LimeTabularExplainer(training_data, mode='classification', training_labels=None, feature_names=None, categorical_features=None, categorical_names=None, kernel_width=None, kernel=None, verbose=False, class_names=None, feature_selection='auto', discretize_continuous=True, discretizer='quartile', sample_around_instance=False, random_state=None, training_data_stats=None)` | `explain_instance(data_row, predict_fn, labels=(1,), top_labels=None, num_features=10, num_samples=5000, distance_metric='euclidean', model_regressor=None)` | `data_row` is one feature vector. `predict_fn` receives a batch and, for classification, returns `(n_rows, n_classes)`. Returns a LIME `Explanation`; `as_list(label=class_id)` is a list of `(feature_description, weight)`, and `as_map()` maps labels to `(feature_id, weight)` pairs. |
| `LimeTextExplainer(kernel_width=25, kernel=None, verbose=False, class_names=None, feature_selection='auto', split_expression='\\W+', bow=True, mask_string=None, random_state=None, char_level=False)` | `explain_instance(text_instance, classifier_fn, labels=(1,), top_labels=None, num_features=10, num_samples=5000, distance_metric='cosine', model_regressor=None)` | `text_instance` is one raw string. `classifier_fn` receives a list of strings and returns `(n_rows, n_classes)`. Returns `Explanation`; `as_list(label=...)` contains token/substring weights. |
| `LimeImageExplainer(kernel_width=0.25, kernel=None, verbose=False, feature_selection='auto', random_state=None)` | `explain_instance(image, classifier_fn, labels=(1,), hide_color=None, top_labels=5, num_features=100000, num_samples=1000, batch_size=10, segmentation_fn=None, distance_metric='cosine', model_regressor=None, random_seed=None)` | `image` is a single image array. `classifier_fn` receives a batch/list of perturbed images and returns `(n_rows, n_classes)`. Returns `Explanation`; `get_image_and_mask(label, positive_only=True, num_features=5, hide_rest=False)` returns an image and a segment mask. |

AIX360's LIME methods simply delegate to the underlying object. For a
classifier, `class_names` is presentation metadata and must be in the same
order as the probability columns. `top_labels` chooses labels from the
callable output; `labels` requests explicit class indices. Set a small
`num_samples` only for a smoke check, not for a quality claim. Use a fixed
`random_state`/`random_seed` when comparing runs.

### LIME adapters

```python
# A sklearn-style classifier: the callable already has the right batch API.
explainer = LimeTabularExplainer(
    X_train, feature_names=feature_names, class_names=class_names,
    mode="classification", random_state=7,
)
exp = explainer.explain_instance(X_test[0], model.predict_proba,
                                 labels=(target_class,), num_features=4,
                                 num_samples=200)
rows = exp.as_list(label=target_class)

# A text pipeline must accept a list of raw strings.
text_exp = LimeTextExplainer(class_names=class_names, random_state=7)
exp = text_exp.explain_instance(text, text_pipeline.predict_proba,
                                 labels=(target_class,), num_features=8,
                                 num_samples=200)

# An image pipeline must preserve a batch of images.
image_exp = LimeImageExplainer(random_state=7)
exp = image_exp.explain_instance(image, image_pipeline.predict_proba,
                                 top_labels=1, num_features=10,
                                 num_samples=100)
image, mask = exp.get_image_and_mask(target_class, positive_only=False,
                                     num_features=10, hide_rest=False)
```

The examples above are contracts, not a promise that every installed LIME
version accepts every optional keyword. If an older LIME rejects a keyword,
inspect its signature and remove only that optional keyword; do not change the
batch/output convention.

## SHAP wrappers

Import from `aix360.algorithms.shap` when the optional `shap` dependency is
available:

| AIX360 wrapper | Constructor delegation | `explain_instance` delegation | Typical use |
|---|---|---|---|
| `KernelExplainer(*argv, **kwargs)` | `shap.KernelExplainer(*argv, **kwargs)` | `self.explainer.shap_values(*argv, **kwargs)` | Model-agnostic callable, including tabular models |
| `LinearExplainer(*argv, **kwargs)` | `shap.LinearExplainer(*argv, **kwargs)` | `shap_values` | Linear/sparse models |
| `TreeExplainer(*argv, **kwargs)` | `shap.TreeExplainer(*argv, **kwargs)` | `shap_values` | Supported tree models |
| `GradientExplainer(*argv, **kwargs)` | `shap.GradientExplainer(*argv, **kwargs)` | `shap_values` | Differentiable model/backend |
| `DeepExplainer(*argv, **kwargs)` | `shap.DeepExplainer(*argv, **kwargs)` | `shap_values` | Deep model/backend |

For the common tabular call, construct `KernelExplainer(model_callable,
background)` and call `explain_instance(X_one_row_or_batch, nsamples=...)`.
The wrapper returns exactly the underlying `shap_values` result. Depending on
SHAP version and model output, this is commonly:

- regression or a single scalar output: `(n_features,)` for one row or
  `(n_rows, n_features)` for a batch;
- historical multiclass classification: a list of `n_classes` arrays, each
  `(n_features,)` for one row or `(n_rows, n_features)` for a batch;
- some newer SHAP releases: an ndarray with a class/output axis instead of a
  list.

Never index `shap_values[0]` as “class zero” until the result type and shape
are inspected. The SHAP wrapper exposes `wrapper.explainer.expected_value` for
base values and the underlying SHAP package for plots. A background sample is
part of the explanation contract; summarize it only when the resulting
approximation is acceptable. `KernelExplainer` can explain a scalar target
callable such as `lambda X: model.predict_proba(X)[:, 1]`, which simplifies
shape and class selection.

## GroupedCE / ICE

Import `GroupedCEExplainer` from `aix360.algorithms.gce`.

```text
GroupedCEExplainer(
    model, data, feature_names=None, n_samples=25,
    features_selected=None, top_k_features=-1,
    feature_importance_method='SHAP', max_dataset_size=10,
    random_seed=None, **kwargs
)
explain_instance(instance, **kwargs)
```

`data` supplies numeric feature ranges and must represent the same feature
order as `instance`. If `feature_names` is omitted, a DataFrame is created and
its column labels are used. `model` should return one real-valued prediction
per perturbed row. For a multiclass classifier, select one probability column
with an adapter before using GroupedCE.

- With one `features_selected` feature, `explain_instance` requires exactly
  one row and returns a dict with `feature_name`, `feature_value` (length
  `n_samples`), `ice_value` (length `n_samples` after squeeze), and
  `current_value`.
- With two or more selected features, it returns a dict with
  `selected_features`. For each ordered feature pair, the nested value has
  `gce_values` as an `n_samples x n_samples` list, `x_grid`, `y_grid`, and,
  by default, `current_values` and `prediction`.
- `return_instances=False` omits the current-value/prediction metadata from
  pairwise results. `feature_perturbations={name: {'min': ..., 'max': ...}}`
  overrides the data-derived range for a selected feature.
- If `features_selected=[]` and `top_k_features > 0`, the implementation uses
  SHAP `KernelExplainer` to rank features. This path therefore needs SHAP and
  a compatible scalar/batch model callable. With `top_k_features <= 0`, all
  features are selected.

Categorical features are not supported by the GroupedCE perturbation path.
Keep `n_samples` small for a smoke check because pairwise work is quadratic.

## NearestNeighborContrastive

Import `NearestNeighborContrastiveExplainer` from
`aix360.algorithms.nncontrastive`. Its key constructor parameters are:

```text
NearestNeighborContrastiveExplainer(
    model=None, n_classes=2, metric='euclidean', neighbors=3,
    embedding_type=EmbeddingType.UNSUPERVISED,
    embedding_dim=8, category_enc_dim=3, category_encoding='ohe',
    numeric_scaling=None, layers_config=[16, 16], ...
)
```

The remaining constructor options control the TensorFlow autoencoder and,
for supervised embeddings, its classifier head. The operational methods are:

```text
fit(x, y=None, features=None, categorical_features=[],
    categorical_values={}, epochs=5, batch_size=128, verbose=0,
    shuffle=True, validation_fraction=0, max_training_records=10000,
    exemplars=None, random_seed=None, **kwargs) -> training history
set_exemplars(x) -> self
explain_instance(x, neighbors=None) -> dict or list[dict]
```

`x` is a DataFrame or array with stable feature order. `categorical_features`
must name columns in `features`; `categorical_values` can enumerate allowed
values. `numeric_scaling` is one of `minmax`, `standard`, or `quantile` when
used. `embedding_type` is supervised or unsupervised; supervised fitting
needs `y` for the embedding constraint, not necessarily the target model's
labels.

The `model` callable is a class-label function. It is used to assign exemplar
classes and remove same-class exemplars, so adapt probabilities explicitly:
`lambda X: np.argmax(model.predict_proba(X), axis=1)`. A one-dimensional query
returns one dict with `features`, `categorical_features`, `query`,
`neighbors`, and `distances`; a two-dimensional query returns one such dict per
row. `neighbors` is a list of feature rows and `distances` has the same length.
Model-free mode uses the user-supplied exemplar set and is only contrastive if
that set was chosen to represent the desired alternate class. Ensure at least
`neighbors` valid exemplars remain after same-class filtering.

## Local metrics

Import `faithfulness_metric` and `monotonicity_metric` from `aix360.metrics`.
Both have the exact signature:

```text
faithfulness_metric(model, x, coefs, base) -> float
monotonicity_metric(model, x, coefs, base) -> bool
```

The implementation calls `model.predict_proba(x.reshape(1, -1))`, selects the
model's predicted class, and compares one-feature-at-a-time replacements with
`base`. Therefore `x`, `coefs`, and `base` must each be one-dimensional and
have the same `n_features`, in the same order. `base` is the replacement
vector, not a background matrix. `coefs` must be the explanation weights for
that same row and feature order. Faithfulness returns a signed correlation
score (higher is not automatically “better” without interpreting the sign and
model behavior); monotonicity returns whether the implementation's ordered
probability sequence is nondecreasing. These helpers are classifier metrics,
not general regression metrics.
