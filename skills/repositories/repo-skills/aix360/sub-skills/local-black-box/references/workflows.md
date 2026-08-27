# Local explanation workflows

These recipes use only caller-owned data and a trained model. They do not
fetch datasets. Start every workflow with an output probe and keep the probe's
class order beside the explanation artifact.

## 1. Preflight any callable

Choose one contract before choosing a method:

```text
LIME classification / text / image: probabilities, shape (n_rows, n_classes)
SHAP scalar target / GroupedCE: scalar scores, shape (n_rows,) or (n_rows, 1)
SHAP multiclass: preserve the underlying class/output axis and inspect it
NN contrastive: integer-like class labels, shape (n_rows,) or (n_rows, 1)
```

For a quick shape-only check, run the bundled helper from this sub-skill:

```bash
python scripts/check_model_output.py --kind probabilities --rows 3 --classes 2
python scripts/check_model_output.py --kind scalar --rows 3
python scripts/check_model_output.py --kind labels --rows 3 --classes 2
```

For a real captured output, pass JSON with the same command, for example:

```bash
python scripts/check_model_output.py --kind probabilities --rows 2 \
  --classes 3 --values '[[0.2, 0.3, 0.5], [0.8, 0.1, 0.1]]'
```

A failed check is useful: fix the adapter or report the incompatibility; do
not reshape a class vector blindly because that can change class semantics.

## 2. Reproducible CPU tabular smoke fixture

This fixture trains a tiny two-class model, runs AIX360's LIME wrapper, checks
its explanation structure, and exercises both local metrics. It is intended as
an API smoke test, not a statistical evaluation.

```python
import numpy as np
from sklearn.linear_model import LogisticRegression
from aix360.algorithms.lime import LimeTabularExplainer
from aix360.metrics import faithfulness_metric, monotonicity_metric

X = np.array([
    [-2.0, -1.0], [-1.5, -0.5], [-1.0, -1.2],
    [ 1.0,  1.2], [ 1.5,  0.5], [ 2.0,  1.0],
], dtype=float)
y = np.array([0, 0, 0, 1, 1, 1])
model = LogisticRegression(random_state=0).fit(X, y)
assert model.predict_proba(X[:2]).shape == (2, 2)

lime = LimeTabularExplainer(
    X, feature_names=["left_right", "up_down"],
    class_names=["negative", "positive"], random_state=0,
)
row = X[4]
label = int(model.predict(row.reshape(1, -1))[0])
exp = lime.explain_instance(row, model.predict_proba,
                            labels=(label,), num_features=2,
                            num_samples=80)
items = exp.as_list(label=label)
assert len(items) > 0
mapping = exp.as_map()[label]
coefs = np.zeros(X.shape[1], dtype=float)
for feature_index, weight in mapping:
    coefs[int(feature_index)] = float(weight)
base = X.mean(axis=0)
faith = faithfulness_metric(model, row, coefs, base)
mono = monotonicity_metric(model, row, coefs, base)
assert np.isfinite(faith)
assert isinstance(mono, (bool, np.bool_))
print({"label": label, "items": items, "faithfulness": float(faith),
       "monotonicity": bool(mono)})
```

If this fails at import, classify it as a LIME or package-environment issue.
If it fails at the metric call, first check that `mapping` covers the same
feature indices as `row` and that `base` is one-dimensional.

## 3. Tabular, text, and image selection

### Tabular

Use `LimeTabularExplainer` when the user needs a human-readable local
surrogate and a small set of feature weights. Use `KernelExplainer` when a
SHAP additive attribution is required or when the model is not supported by a
model-specific SHAP explainer. For either method:

1. Keep preprocessing inside the model callable.
2. Use a representative background for SHAP; do not use the explained row as
   the only background without documenting the consequence.
3. For multiclass models, either explain every class explicitly or adapt one
   class to a scalar output.
4. Check one-row and batch calls separately because output dimensions differ.

### Text

Give LIME raw text and a pipeline callable that accepts `list[str]`. Do not
pre-tokenize the text unless the callable itself expects that representation.
Set `class_names` in probability-column order and inspect `exp.as_list()` for
tokens/substrings. For sparse vectorizers, preserve the sparse matrix inside
the pipeline; the LIME text callable still receives raw strings.

### Image

Give LIME one image array and a classifier callable that accepts a batch of
perturbed images. Define a segmentation function only when the image domain
needs a custom segmentation. Check the returned mask dimensions before
overlaying it. Avoid claiming a meaningful visual explanation when the model
preprocessing changes channel order, scale, or image shape between the model
and LIME.

SHAP `DeepExplainer`/`GradientExplainer` can be considered only after verifying
the installed SHAP and TensorFlow/Keras compatibility with the model. These
wrappers do not repair channel or preprocessing mismatches.

## 4. Scalar SHAP and GroupedCE

For a classifier with `n_classes`, select one target probability explicitly:

```python
from aix360.algorithms.shap import KernelExplainer
from aix360.algorithms.gce import GroupedCEExplainer

target = 1
def target_score(batch):
    return model.predict_proba(batch)[:, target]

shap_exp = KernelExplainer(target_score, X_background)
values = shap_exp.explain_instance(X_one_row, nsamples=100)
# Check values.shape == (n_features,) for one row, or inspect the version.

gce = GroupedCEExplainer(
    model=target_score, data=X_background,
    feature_names=feature_names, features_selected=[feature_names[0]],
    n_samples=12, random_seed=0,
)
ice = gce.explain_instance(X_one_row.reshape(1, -1))
assert len(ice["feature_value"]) == 12
assert len(ice["ice_value"]) == 12
```

For pairwise GCE, select two or more numeric names and expect one grid per
ordered pair. If `top_k_features` is used instead, record that SHAP is an
additional dependency and that ranking is performed during `fit`.

## 5. Nearest-neighbor contrastive workflow

Use this only when an embedding and exemplar semantics are acceptable:

1. Put the training rows in a DataFrame with stable feature names.
2. Mark categorical columns and their allowed values; choose a numeric scaler
   when raw feature scales would dominate the embedding.
3. Instantiate with a small `embedding_dim`, `layers_config`, `neighbors`, and
   fixed seed for a smoke run.
4. Call `fit`; pass `exemplars` explicitly when model-free contrast is needed.
5. If a black-box classifier is supplied, adapt `predict_proba` to integer
   labels with `argmax`, then call `explain_instance` on one row.
6. Assert that returned neighbor and distance lists have equal length and
   re-run the model on a neighbor to verify the contrastive class.

Fitting uses TensorFlow and can be slow or unavailable. A successful import of
the class is not proof that `fit` can build its autoencoder. Record epochs,
backend, and whether same-class filtering left enough exemplars.

## 6. Visualization and reporting

Keep numeric explanation objects as the primary artifact. For LIME, report
`as_list`/`as_map` or the image mask. For SHAP, report the values, expected
value/base value, feature order, output class, and the plotting library/version
separately. For GroupedCE, report grids and current values; for NN contrastive,
report query, neighbor rows, distances, and the class convention.

Every report should distinguish:

- model output and explanation target;
- sampled/perturbed inputs and reference/background data;
- class or feature-name mapping;
- dependency/backend status;
- a local sanity check or metric result;
- limitations such as approximation, sparse support, segmentation, or
  non-actionable contrastive examples.
