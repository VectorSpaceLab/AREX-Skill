# API reference

This reference is an operating summary of the AIX360 0.3.0 interfaces in this
skill. Examples use the public import paths and intentionally small in-memory
arrays or pandas frames. Use `inspect.signature` in the validated environment
when a local installation differs; do not infer a missing optional backend from
an import name alone.

## Common data contracts

| Object | Required input | Main output | Important state |
|---|---|---|---|
| `FeatureBinarizer` | pandas `DataFrame` | binary `DataFrame` with a 3-level `MultiIndex` `(feature, operation, value)` | `maps`, `enc`, `thresh`, `NaN`, optionally `ordinal`, `scaler` |
| `FeatureBinarizerFromTrees` | pandas `DataFrame` plus `y` for `fit` | selected binary `DataFrame`, optionally `(binary, standardized ordinal)` | `features`, `maps`, `enc`, `thresh`, `ordinal`, optional `scaler` |
| `ProtodashExplainer` | finite numeric 2-D `X`, candidate 2-D `Y`, integer `m` | `(W, S, objective_values)` | `S` indexes rows of `Y`; `W` is not normalized |
| `BRCGExplainer` | fitted `BooleanRuleCG`, binary frame, binary target | labels; `dict` from `explain` | underlying model has `z`, `w`, `CNF` |
| `GLRMExplainer` | fitted linear/logistic rule regressor and binarized frame | predictions; coefficient `DataFrame` | underlying model has selected conjunction matrix `z` |
| `RipperExplainer` | pandas frame and pandas `Series` | labels; TRXF `DnfRuleSet` | target label, default label, encoded nominal columns |
| `IMDExplainer` | same-row feature frame and two aligned prediction arrays | diff rules/regions and metrics | joint surrogate tree, `diffrules`, `diffregions` |
| `TED_CartesianExplainer` | estimator, features, labels, dense explanation ids | label/explanation pair | combined label space and `NumE` |

Use a single feature schema from fit through evaluation. Do not turn a
MultiIndex into strings before calling BRCG/GLRM; their conjunction algebra
uses the levels and their values. Keep the original frame as well if a
human-readable rule or TRXF assignment is needed.

## Feature binarizers

### Quantile/unique-threshold binarization

```python
from aix360.algorithms.rbm import FeatureBinarizer
fb = FeatureBinarizer(
    colCateg=["plan"], numThresh=3,
    negations=True, threshStr=False, returnOrd=True
)
Xb_train, Xstd_train = fb.fit_transform(X_train)
Xb_test, Xstd_test = fb.transform(X_test)
```

`FeatureBinarizer.fit(X)` returns the transformer. `transform(X)` returns a
binary frame, or `(binary, standardized_ordinal)` when `returnOrd=True`.
Binary/constant columns use mappings; object or declared categorical columns
use one-hot equality tests; numeric columns use unique thresholds for small
cardinality or quantiles for larger cardinality. With missing numeric values,
threshold indicators are zeroed for missing rows and a `NaN` indicator is
added. Unknown categorical values are ignored by the encoder, which means all
known equality indicators can be zero.

`negations=True` adds inverse tests. `threshStr=True` converts threshold values
in the MultiIndex to strings for display. Use `returnOrd=True` only when the
GLRM model is configured with `useOrd=True`; pass the matching standardized
frame as `Xstd` to `fit`, `predict`, and `predict_proba`.

### Tree-derived binarization

```python
from aix360.algorithms.rbm import FeatureBinarizerFromTrees
fbt = FeatureBinarizerFromTrees(
    colCateg=["plan"], treeNum=2, treeDepth=3,
    treeFeatureSelection="sqrt", threshRound=4,
    returnOrd=True, randomState=7
)
fbt.fit(X_train, y_train)
Xb_train, Xstd_train = fbt.transform(X_train)
Xb_test, Xstd_test = fbt.transform(X_test)
```

`fit(X, y)` is mandatory. Categorical and binary columns are prepared in the
FeatureBinarizer style; ordinal columns are supplied to decision trees and the
observed tree split thresholds become paired `<=` and `>` binary features.
`features` is the sorted MultiIndex of retained tests. `treeNum`, `treeDepth`,
`treeFeatureSelection`, `treeKwargs`, `threshRound`, `threshStr`,
`returnOrd`, and `randomState` control the extracted feature set. `treeDepth`
must be `None` or a positive integer; `treeNum` must be positive; feature
selection accepts `None`, `auto`, `sqrt`, `log2`, or a proportion in `(0, 1]`.

Missing values and `y=None` are rejected during fit. Transform can compare
missing values, but their indicators must be part of the deliberately chosen
schema. Before transforming, check that every column used at fit is present
and has compatible meaning; a renamed or dropped column should fail loudly.

## ProtoDash

```python
from aix360.algorithms.protodash import ProtodashExplainer
explainer = ProtodashExplainer()
weights, indices, history = explainer.explain(
    X_summary_target, Y_candidate_pool, m=3,
    kernelType="other", sigma=2, optimizer="osqp"
)
prototypes = Y_candidate_pool[indices]
```

Signature: `explain(X, Y, m, kernelType='other', sigma=2,
optimizer='cvxpy')`. `kernelType='Gaussian'` computes a Gaussian similarity
with width `sigma`; other values use inner products. `optimizer` is `cvxpy` or
`osqp`. `indices` are selected row positions in `Y`; `weights` correspond to
the selected prototypes and are non-negative, unnormalized importance
weights. The third result tracks objective values during greedy selection.
Inputs are observations by features and must have matching finite feature
semantics. Prototype selection is not a fitted predictive classifier and does
not provide a `predict` method.

The helper for XPT files is not part of the normal portable workflow. If such
data are used, validate parsing and one-hot encoding separately; `xport` is an
optional import-time dependency and historical encoder keyword names vary by
scikit-learn version.

## BRCG and GLRM

### BRCG

```python
from aix360.algorithms.rbm import BooleanRuleCG, BRCGExplainer
brcg = BRCGExplainer(BooleanRuleCG(
    lambda0=0.001, lambda1=0.001, CNF=False,
    iterMax=50, timeMax=20, K=5, D=4, B=3,
    solver="ECOS", silent=True
))
# If ECOS is unavailable, choose one name from cvxpy.installed_solvers().
brcg.fit(Xb_train, y_train)
y_hat = brcg.predict(Xb_test)
rule_info = brcg.explain(maxConj=10, prec=3)
```

The model fits a directly interpretable binary classifier. `CNF=False` gives
a DNF-style positive rule set; `CNF=True` reverses the internal target and
reports the CNF flag. `fit` mutates the wrapped model and, in this AIX360
version, the explainer wrapper does not reliably return itself, so retain the
object created before fitting. `predict` returns binary labels. `explain`
returns `{'isCNF': bool, 'rules': list[str]}`. Inspect
`brcg._model.z`, the selected positive columns in `brcg._model.w`, and the
reported rules to count clauses; do not treat every generated column as a
selected rule.

### GLRM

```python
from aix360.algorithms.rbm import GLRMExplainer, LogisticRuleRegression
model = LogisticRuleRegression(
    lambda0=0.05, lambda1=0.01, useOrd=True,
    debias=True, maxSolverIter=500
)
glrm = GLRMExplainer(model)
glrm.fit(Xb_train, y_train, Xstd_train)
y_hat = glrm.predict(Xb_test, Xstd_test)
p_hat = glrm.predict_proba(Xb_test, Xstd_test)
coefficients = glrm.explain(maxCoeffs=20, highDegOnly=False, prec=3)
```

`LinearRuleRegression` has the same fit/predict/explain shape for continuous
targets. `LogisticRuleRegression` additionally has `predict_proba`; its
probability is for class 1. If `useOrd=False`, omit `Xstd` everywhere. If
`useOrd=True`, pass the same ordinal columns and scaling state from the fitted
transformer. `explain` returns a `DataFrame` with rule or numerical-feature
names and coefficients; the intercept is included. `highDegOnly=True` filters
to higher-degree conjunctions. `visualize(Xorig, fb, features=None)` is
optional plotting support and is not required for a portable rule artifact.

Important tuning controls include `lambda0` (per-rule cost), `lambda1`
(per-literal cost), `K`, `iterMax`, `B`, `wLB`, `stopEarly`, `eps`, and (for
logistic models) `maxSolverIter`. Larger complexity penalties and smaller
search budgets usually produce shorter but less expressive rules. Check that
the selected `z` is not empty and that predictions are not a constant caused
by degenerate targets.

## RIPPER and TRXF

```python
from aix360.algorithms.rule_induction.ripper import RipperExplainer
ripper = RipperExplainer(d=64, k=2, pruning_threshold=20, random_state=0)
ripper.fit(X_train, y_train, target_label=positive_label)
y_hat = ripper.predict(X_test)
ruleset = ripper.explain()          # TRXF DnfRuleSet
```

RIPPER requires pandas `DataFrame`/`Series` because it retains feature names
and handles nominal values. A supplied `target_label` requires a binary target
and selects that label as positive. Without it, the algorithm induces ordered
rules for multiple labels; use `explain_multiclass()` for a list of TRXF rule
sets rather than `explain()`.

TRXF primitives are public and typed:

```python
from aix360.algorithms.rule_induction.trxf.core import (
    Feature, Predicate, Relation, Conjunction, DnfRuleSet
)
rule = DnfRuleSet([
    Conjunction([
        Predicate(Feature("age"), Relation.GE, 18),
        Predicate(Feature("segment"), Relation.EQ, "new"),
    ])
], then_part="approved")
rule.evaluate({"age": 21, "segment": "new"})
```

`Feature` accepts arithmetic expressions using names, constants, `+`, `-`,
`*`, `/`, and parentheses. `Predicate` supports `!=`, `==`, `<`, `<=`, `>`,
`>=`; strings and booleans may only use equality or inequality. A
`Conjunction` is AND; `DnfRuleSet` is OR and carries one `then_part`. Preserve
these values and relations when persisting rules. The optional
`RuleSetClassifier` applies `FIRST_HIT`, `WEIGHTED_MAX`, or `WEIGHTED_SUM`
conflict resolution and can add rule metrics before export.

PMML export requires a compatible TRXF reader with a non-null data dictionary
and a serializer (normally `NyokaSerializer`). Build the data dictionary from
the exact feature schema and categorical values. An unsupported feature
expression or serializer object should be reported and reduced to a plain
JSON-like rule representation rather than forced through PMML.

## IMD

```python
from aix360.algorithms.imd.imd import IMDExplainer
imd = IMDExplainer()
imd.fit(
    X_train, model_a.predict(X_train), model_b.predict(X_train),
    max_depth=5, split_criterion=1, alpha=0.0, verbose=False
)
rules = imd.explain()                 # list of Rule objects
regions = imd.diffregions            # feature -> [observed lower, upper]
report = imd.metrics(
    X_test, model_a.predict(X_test), model_b.predict(X_test), name="test"
)
```

IMD is for two already fitted classifiers. Inputs must have equal row order and
feature columns for both output arrays. The learned joint surrogate tree
makes shared prefixes where possible and diverges in regions where outputs
differ. `Rule` objects expose `predicates`, `class_label`, `as_string()`,
`as_dict()`, `apply()`, `filter()`, and `intersection()`. `diffregions` are
closed numeric ranges derived from the observed training domain and are best
read as surrogate regions, not causal guarantees. `metrics` reports observed
diffs, precision, recall, rule count, and unique predicate count. Division by
zero can occur when there are no diffs or no region hits; handle that case
before presenting rounded metrics.

Graph drawing is optional. The rule and region outputs work without graphviz;
only invoke graph rendering after checking the optional native dependency.

## TED Cartesian

```python
from aix360.algorithms.ted import TED_CartesianExplainer
from sklearn.svm import SVC
ted = TED_CartesianExplainer(SVC(kernel="linear"))
ted.fit(X_train, y_train, explanation_ids_train)
y_hat, e_hat = ted.predict_explain(X_test)
labels = ted.predict(X_test)
explanations = ted.explain(X_test)
score = ted.score(X_test, y_test, explanation_ids_test)
```

TED composes `Y` and `E` as `YE = Y * NumE + E`, where `NumE = max(E)+1`,
then trains the supplied estimator on `YE`. Explanation ids must be dense
non-negative integer codes; if they are strings or sparse ids, encode them
explicitly and retain the decoder. `predict_explain` returns `(Y, E)` by
integer division/modulo. `score` returns combined-label, label, and
explanation accuracy. TED teaches a joint label/explanation prediction; it is
not a post-hoc explanation of an independently trained opaque predictor.

## CoFrNet, DIPVAE, ProfWeight

These APIs are optional and should be used only after a backend probe.

| Method | Construction | Useful result | Boundary |
|---|---|---|---|
| CoFrNet | `generate_connections(...)` then `CoFrNet_Model(connections)`; wrap with `CoFrNet_Explainer` | masked continued-fraction network; `explain("importances")` or `explain("print_co_fr", ...)` | PyTorch model; training helper is a simple tabular loop, not a general estimator |
| DIPVAE | `DIPVAEExplainer(model_args, dataset=..., net=..., cuda_available=...)` | `fit()` ELBO history; `explain(input_images, edit_dim_id, edit_dim_value, edit_z_sample=False)` returns decoded edits | PyTorch/torchvision; model args and dataset methods are mandatory |
| ProfWeight | `prof_weight_compute(files, start, end, y_one_hot)` then `ProfweightExplainer.fit(...)` or `explain(...)` | per-sample confidence weights and weighted simple model | legacy Keras/TensorFlow training callback and checkpoint contract |

`generate_connections` variants include `fully_connected`, `diagonalized`,
`ladder_of_ladders`, `diag_ladder_of_ladder_combined`, `one_feature_diag`, and
`n_feature_fully_connected`. CoFrNet expects a connection list with compatible
shapes; its activation uses a capped reciprocal and can be numerically
sensitive around zero. DIPVAE needs model-specific args such as latent size,
layer counts, learning rate, epochs, and covariance penalties; the dataset
must provide dimensions, likelihood/output activation, instance count, and
`next_batch()`. ProfWeight expects probe `.npy` arrays with matching sample
and class dimensions, one-hot labels, an inclusive layer range, and a simple
Keras model factory plus hyperparameters such as optimizer, checkpoint path,
batch size, epochs, class count, and learning-rate callbacks.
