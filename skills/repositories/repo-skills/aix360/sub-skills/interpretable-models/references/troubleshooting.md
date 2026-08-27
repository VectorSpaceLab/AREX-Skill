# Troubleshooting

Use the first failing boundary as the diagnosis. Do not mask a schema or
solver error with a new imputer, a different target encoding, or a different
optimizer without recording the change.

## Feature schema and transformation

### `KeyError`, missing feature, or incompatible column

`FeatureBinarizerFromTrees.transform` iterates over the learned MultiIndex and
indexes the original feature column. A selected feature missing from the new
frame therefore fails rather than meaningfully disappearing. This commonly
happens when a caller drops a column after fit, changes a spelling, or supplies
only the transformed columns instead of the original frame.

Recovery:

1. Compare `set(fitted_input_columns) - set(new.columns)` and report the exact
   names before transform.
2. Restore the missing column using the same preprocessing and dtype used at
   fit, or refit the transformer on the intentionally reduced schema.
3. Do not add a fabricated constant column unless that constant is part of a
   documented preprocessing contract.
4. Assert `list(X_train.columns) == list(X_eval.columns)` and retain
   `transformer.features`/`transformer.ordinal` in the schema manifest.

`FeatureBinarizer` can ignore unknown categorical levels because its encoder
uses `handle_unknown='ignore'`, but this is not the same as a missing source
column. Treat all-zero known category indicators as an explicit unknown-level
case and monitor its frequency.

### NaN/None and categorical data

`FeatureBinarizerFromTrees.fit` rejects missing values in `X` and `y`; its
categorical path also rejects categorical NaN. Decide whether to impute, add a
missing indicator, or remove a row before fitting. For ordinary
`FeatureBinarizer`, numeric missing rows receive zero threshold indicators and
a `NaN` indicator; categorical unknown values may produce no equality hit.
Never let train and evaluation use different missing semantics. RIPPER has its
own nominal encoding and dtype assumptions; use float for continuous features
and preserve the original categorical values.

### MultiIndex feature names look wrong

Do not flatten `(feature, operation, value)` before BRCG/GLRM fit. If a human
export needs strings, create a separate display table. If `threshStr=True`,
remember that values are strings in transformed column labels; preserve this
choice when inspecting or serializing rules.

## cvxpy and solver failures

### BRCG: solver missing, infeasible, or no clauses

BRCG constructs a cvxpy LP and defaults to `solver='ECOS'`. A missing ECOS
installation, incompatible cvxpy version, solver status failure, or a constant
class target can result in an exception or unusable weights.

Recovery:

1. Probe `cvxpy.installed_solvers()` and choose an actually installed solver
   accepted by the environment. Keep `verbose=True` for the first diagnosis.
2. Reduce `D`, `K`, `B`, `iterMax`, and `timeMax` for a bounded smoke run; use
   finite binary data and both target classes.
3. Check `np.isfinite(Xb.to_numpy()).all()` and target cardinality before fit.
4. After fit inspect `model.w`, `model.wLP`, `model.z`, `model.it`, and
   `explain()['rules']`. An empty selected set can be a valid result for a
   weak/degenerate problem; compare with a constant baseline.
5. If the selected solver still fails, preserve a clear blocked status rather
   than silently switching to a different model family.

### ProtoDash: cvxpy/OSQP failure or degenerate weights

ProtoDash's quadratic subproblem accepts only `optimizer='cvxpy'` or
`'osqp'`. NaN/infinite data, a non-positive-semidefinite numerical kernel,
identical candidate rows, `m > len(Y)`, or an unavailable solver can produce
failure, repeated selections, NaN weights, or nearly all-zero weights.

Recovery:

1. Validate 2-D finite arrays, matching feature semantics, `1 <= m <= len(Y)`,
   and a positive Gaussian `sigma`.
2. Standardize or scale very large features consistently in `X` and `Y`.
3. Retry with `optimizer='osqp'` or `'cvxpy'` only after checking availability;
   record the selected optimizer and solver status.
4. Deduplicate exact candidate rows when repeated prototypes have no semantic
   value, or accept duplicates explicitly with source ids.
5. Treat small negative values caused by tolerance as numerical noise only
   after checking magnitude; do not normalize a fundamentally degenerate
   weight vector. Reduce `m` and inspect objective history.

### GLRM logistic solver convergence

`LogisticRuleRegression` uses scikit-learn `saga`. If it reaches
`maxSolverIter`, increase that bound only after checking feature scale and
class balance. Reduce rule search (`K`, `iterMax`, `B`) and use a fixed seed in
the surrounding split. If `predict_proba` is unavailable, check that the
wrapped model is logistic rather than linear; the GLRM wrapper raises a
`ValueError` for a model without that method.

## xport and `pkg_resources`

ProtoDash imports `xport` at module import because its legacy XPT helper is
bundled. A modern setuptools may warn that `pkg_resources` is deprecated, or a
newer xport may fail to import. For ordinary numeric-array ProtoDash, this is a
packaging boundary, not a reason to read an XPT file.

Recovery:

1. Record the warning/error and check the installed xport/setuptools pair.
2. Use the array API with a local DataFrame/NumPy preprocessing path when the
   module import itself succeeds.
3. If import fails because xport is absent/broken, install a compatible
   environment or mark ProtoDash blocked; do not copy the XPT helper into
   runtime files or silently reinterpret its missing-data convention.
4. Avoid pinning a global setuptools version from inside a workflow. Keep any
   legacy pin isolated to the optional environment and document it.

## Rule serialization and unsupported objects

TRXF rule objects are executable typed objects, not universally pickle-safe or
PMML-safe strings. PMML export additionally needs a data dictionary, supported
field types, and a compatible Nyoka serializer. Unsupported arithmetic,
object-valued predicates, custom classes, or missing categorical values can
fail during reader/serializer conversion.

Recovery:

1. Validate every `Feature` expression and every `Predicate` relation/value
   against the serializer's supported data types.
2. Build the data dictionary from the exact training schema; include observed
   categorical values and correct continuous/ordinal types.
3. Export a small ruleset first, parse/round-trip it, and compare predictions
   on representative assignments.
4. If an object cannot be serialized, stop PMML export and emit a portable
   JSON-like record: `then_part`, ordered conjunctions, feature expressions,
   relation names, and typed values. Do not stringify a custom object's memory
   address or use `repr` as a future parser.
5. Preserve rule evaluation through TRXF as the reference behavior and state
   that PMML was intentionally excluded.

## Graphviz and pygraphviz

IMD rule fitting, `diffrules`, `diffregions`, and `metrics` do not require graph
rendering. `visualize_jst` eventually uses NetworkX's AGraph bridge and needs a
working graphviz executable plus pygraphviz. A Python `graphviz` package alone
may not supply the native library.

Recovery:

1. Run the textual IMD workflow and save rules/regions first.
2. Probe both the Python module and the native `dot` executable.
3. Install pygraphviz through the platform's supported package manager in the
   optional environment if a graph image is truly required.
4. If native setup is unavailable, omit the image and report the textual
   artifact; do not make visualization a fit gate.

## Legacy TensorFlow/Keras and PyTorch methods

### ProfWeight

The source imports standalone Keras and uses callback names and validation
arguments associated with Keras 2.3.1/TensorFlow 1.14. Modern `keras`,
TensorFlow 2, checkpoint file formats, `val_acc`, or callback signatures are
not guaranteed to work.

Recovery: isolate the historical environment; probe `keras`, TensorFlow,
checkpoint callback, and a one-batch simple model before reading probe arrays.
Validate probe shapes, inclusive layer indices, one-hot labels, and finite
weights with `prof_weight_compute`. If the backend cannot be reproduced,
provide the conceptual profile-weight contract and exclude a training result.

### CoFrNet and DIPVAE

These modules import PyTorch at module load. Missing torch/torchvision is an
optional-backend block. CoFrNet's custom masked linear layers require compatible
connection shapes and use a capped reciprocal that can overflow near zero.
DIPVAE requires a model-args namespace and dataset methods not supplied by the
explainer itself; incorrect likelihood/output activation or latent indices
fails late.

Recovery: run a CPU import and tiny forward pass first, check connection and
latent dimensions, use finite normalized inputs, call `torch.isfinite` on
outputs/ELBO, and only then enable GPU. Do not claim that the source's tabular
training helper is a general pipeline. For an unavailable backend, retain
architecture and API guidance but mark execution unverified.

## IMD and TED edge cases

- IMD requires two output arrays with the same length as `X`. With no training
  disagreements, precision/recall denominators can be zero; report counts and
  `undefined` rather than inventing 0 or 1.
- IMD regions use observed min/max values and numeric predicates. Categorical,
  encoded, or differently scaled columns need an explicit numeric encoding
  contract.
- TED computes `NumE = max(E)+1`; empty, negative, non-integer, or sparse
  explanation ids violate the contract. Re-encode them densely and keep the
  mapping. The base estimator must support composite labels and its test input
  shape.

## Runtime hygiene

Run `python scripts/feature_binarizer_smoke.py --help` first. The helper uses
only in-memory data, writes no files by default, and exercises fit/transform,
missing-column detection, feature names, and a tiny BRCG/GLRM path only when
requested. Keep generated plots, checkpoints, probe arrays, and review logs
outside this runtime skill tree.
