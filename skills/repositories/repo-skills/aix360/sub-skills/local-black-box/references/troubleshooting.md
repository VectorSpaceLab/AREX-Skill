# Local black-box troubleshooting

## Installation and import triage

1. Check the base package and the optional library independently:

   ```bash
   python -c "import aix360; print(aix360.__version__)"
   python -c "import lime; print('lime ok')"
   python -c "import shap; print('shap ok')"
   python -c "import tensorflow as tf; print(tf.__version__)"
   ```

2. Install only the extra for the requested route in an isolated environment.
   The relevant AIX360 extras are `lime`, `shap`, `gce`, and
   `nncontrastive`; the latter two add their own transitive requirements.
3. Re-run the exact import and a tiny callable probe after installation. Keep
   the Python version, package versions, and exception text in the report.
4. Do not interpret a successful `import aix360` as proof that optional
   algorithms are available. The SHAP module imports the external `shap`
   package, and GroupedCE imports SHAP at module import time. A missing SHAP
   package can therefore block both `aix360.algorithms.shap` and
   `aix360.algorithms.gce`.

The package metadata for this release contains historical TensorFlow/Keras
pins for some SHAP/neural extras and a TensorFlow 2.9.3 pin for
`nncontrastive`. Those constraints can conflict with a modern Python stack.
Use a separate compatible environment when that backend is required; do not
replace a failed backend with an unverified claim. If only local tabular/text
explanations are needed, LIME is usually the lower-dependency fallback.

## Missing optional dependency

- **`lime` missing:** install the `lime` extra, or route to an available SHAP
  method after validating SHAP. Do not import the AIX360 LIME wrappers before
  the external library is present.
- **`shap` missing:** install the `shap` extra only if its dependency set is
  compatible. Otherwise use LIME for the local explanation and disclose that
  SHAP/GroupedCE are unavailable. Do not vendor a fake SHAP result.
- **TensorFlow missing:** LIME and SHAP Kernel/Linear/Tree paths may still be
  usable. NN contrastive `fit`, and SHAP Gradient/Deep paths for neural models,
  need a compatible backend. Class construction alone is not a fit test.
- **Image segmentation import missing:** keep the image callable and explain
  with an available segmenter, or report that image LIME is unavailable. Do
  not silently treat raw pixels as meaningful semantic regions.

## Callable and output-shape errors

### LIME classification error

Symptoms include an index error, a class-count mismatch, or a failure inside a
classifier function. Check:

- the callable accepts a batch, not one row only;
- output is numeric, finite, and exactly `(n_rows, n_classes)`;
- every row represents the same class order and, for `predict_proba`, sums to
  approximately one;
- `class_names`, explicit `labels`, and any target label are in range.

For a binary model returning a single score, adapt it to two columns only when
the score truly is `P(class=1)` and the complementary probability can be
formed safely. Otherwise use a scalar SHAP/GroupedCE target, not LIME's
classification path.

### SHAP output ambiguity

The AIX360 SHAP wrappers return the underlying `shap_values` object unchanged.
Print/type-check `type(values)`, `np.asarray(values).shape` where safe, and the
model output shape. Historical multiclass SHAP often returns one array per
class; newer versions can place the output axis in an ndarray. Preserve the
class axis and feature order. Use `wrapper.explainer.expected_value` to map
base values to the same output target.

### GroupedCE prediction mismatch

GroupedCE first tries `model(perturbed_batch)` and then falls back to one row at
a time. A model that returns `(n_rows, n_classes)` will be squeezed into an
ambiguous grid. Adapt it to one scalar class probability or regression score.
Ensure `instance` is exactly one row and contains all named columns in the
same order as `data`; selected features must be numeric.

### NN contrastive class mismatch

The NN implementation converts model outputs to integer labels and filters
same-class exemplars. Passing probabilities causes an invalid or meaningless
class assignment. Adapt with `argmax` for a probability classifier and verify
that the adapter returns one label per row. After filtering, `neighbors` must
not exceed the number of valid exemplars. If the result has no neighbors, add
exemplars for the alternate class or use model-free mode with an explicit
exemplar set.

## Feature names and class names

- Tabular feature names must match the number and order of columns passed to
  the model. Categorical metadata must use the column indices expected by the
  installed LIME version.
- Text `as_list` descriptions are tokens/substrings, not fixed numeric column
  indices. Keep the tokenizer/split expression and model pipeline together.
- Image masks index LIME segments, not necessarily individual pixels or
  channels. Check the mask shape and segmentation convention before labeling
  regions.
- `class_names` is only a display mapping but must have one entry per output
  class. A mismatch can make an otherwise valid explanation appear to belong
  to the wrong class.
- GroupedCE names must all be present in the reference data and query frame;
  missing or nonnumeric names should be fixed at the data contract, not
  caught by dropping columns.
- NN contrastive `features` and `categorical_features` are returned in the
  embedding's feature order. Use them to label neighbor values; do not assume
  the original DataFrame index is returned.

## Sparse, text, and image inputs

- Keep a sparse matrix sparse for a sparse linear model. Do not densify a large
  text vocabulary merely to satisfy a display helper. LIME text should receive
  raw strings and let the pipeline create sparse vectors.
- SHAP Kernel and Linear support depends on the installed SHAP version and
  masker/background implementation. Test one row before explaining a batch.
- For text, the classifier callable must accept `list[str]`; a callable that
  accepts a single string will fail when LIME generates perturbations.
- For images, the classifier callable must accept a batch of identically shaped
  arrays, preserve channel order and preprocessing, and return probabilities.
  A segmentation failure is separate from a model failure.
- GroupedCE and NN contrastive are structured/tabular APIs. Do not pass raw
  text or image tensors to them and expect meaningful feature semantics.

## Local metric argument alignment

Both local metrics call `predict_proba` and reshape `x` to one row. Before
calling either metric, assert:

```python
assert x.ndim == 1
assert coefs.ndim == 1 and base.ndim == 1
assert len(x) == len(coefs) == len(base)
```

Use the same feature order used to generate `coefs`; if LIME's `as_map()` only
contains selected features, initialize a full-length zero vector and place
weights by feature id before calling the metric. `base` must be one value per
feature, not a matrix of background rows. A regression model or a classifier
with only `predict` is not compatible with these package helpers without a
separately justified adapter. If the correlation is NaN, inspect constant
probability sequences, zero-variance coefficients, and whether the target
class changes during feature replacement. Treat monotonicity as a boolean
sanity check, not a universal quality score.

## Recovery stop conditions

Stop and report an unresolved limitation when the required optional package
cannot be installed compatibly, when the model cannot expose the required
batch callable, when class/feature semantics are unknown, or when no valid
alternate exemplars remain. A smaller LIME/CPU fixture can verify the route's
wiring, but it cannot validate the unavailable SHAP, TensorFlow, image, or
large-data behavior.
