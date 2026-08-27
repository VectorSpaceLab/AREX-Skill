# sklearn Workflows

The preferred AIF360 interface is `aif360.sklearn`: pandas objects plus sklearn-style functions and estimators. Keep protected attributes in the index unless an API explicitly takes separate `prot_attr` arrays.

## Standardize or fetch pandas data

### Standardize a user DataFrame

Use `standardize_dataset` when the caller provides one DataFrame with labels, protected attributes, and optional weights.

```python
from aif360.sklearn.datasets import standardize_dataset

bundle = standardize_dataset(
    df,
    prot_attr=["sex", "race"],
    target="approved",
    sample_weight="weight",
    dropcols=["record_id"],
    dropna=True,
)
X, y, sample_weight = bundle.X, bundle.y, bundle.sample_weight
assert X.index.names == ["sex", "race"]
assert y.index.equals(X.index)
```

Key rules:

- Protected attribute labels are copied into the index. Dropping them from feature columns does not remove them from `X.index` or `y.index`.
- `usecols`, `dropcols`, `numeric_only`, and `dropna` are applied in that order.
- If `sample_weight` is omitted, the namedtuple has only `X` and `y`; do not unpack three values.
- If protected attributes are passed as arrays rather than column labels, those arrays become index levels but are not added to feature columns.

### Use fetchers carefully

Use fetchers when the task truly needs one of AIF360's built-in sklearn datasets. They return pandas objects in the same index convention, but first use can require network access or a warmed cache.

```python
from aif360.sklearn.datasets import fetch_adult, fetch_german

adult = fetch_adult(subset="train", cache=True, numeric_only=True)
X, y, sample_weight = adult.X, adult.y, adult.sample_weight

german = fetch_german(cache=True, numeric_only=True)
X_german, y_german = german.X, german.y
```

Fetcher caveats:

- Pass `data_home` to control cache location without depending on any checkout path.
- `fetch_adult`, `fetch_german`, and `fetch_bank` can use OpenML. `fetch_compas`, `fetch_meps`, and `fetch_lawschool_gpa` can download public data files. Avoid fetchers in no-network smokes.
- `fetch_meps` can prompt for terms; only set `accept_terms=True` when the caller explicitly accepts those terms.
- The Law School GPA loader is a regression workflow. Do not treat its target as binary unless the caller defines a valid binarization.

## Preserve protected indexes through sklearn preprocessing

Many sklearn transformers accept DataFrames but return NumPy arrays and strip indexes. Re-wrap transformed arrays before an AIF360 metric, estimator, or postprocessor needs protected attributes.

```python
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder

encoder = make_column_transformer(
    (OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_mask),
    remainder="passthrough",
    verbose_feature_names_out=False,
)
Xt = encoder.fit_transform(X_train)
X_train_enc = pandas.DataFrame(
    Xt,
    columns=encoder.get_feature_names_out(),
    index=X_train.index,
)
```

If a downstream AIF360 call reports that protected attributes are missing, inspect `X.index.names` and `y.index.names` immediately before the call.

## Compute metrics and sklearn scorers

### Direct group metrics

```python
from aif360.sklearn.metrics import (
    statistical_parity_difference,
    disparate_impact_ratio,
    equal_opportunity_difference,
    average_odds_difference,
    average_odds_error,
)

spd = statistical_parity_difference(
    y_true, y_pred,
    prot_attr="sex", priv_group="Male", pos_label=1,
    sample_weight=sample_weight,
)
di = disparate_impact_ratio(
    y_true, y_pred,
    prot_attr="sex", priv_group="Male", pos_label=1,
    zero_division=0,
)
eod = equal_opportunity_difference(y_true, y_pred, prot_attr="sex", priv_group="Male")
aod = average_odds_difference(y_true, y_pred, prot_attr="sex", priv_group="Male")
aoe = average_odds_error(y_true, y_pred, prot_attr="sex", priv_group="Male")
```

Interpretation hints:

- Difference metrics are usually best near zero.
- Ratio metrics are usually best near one; values below the chosen policy threshold indicate disparity.
- With `y_pred=None`, `statistical_parity_difference` and `disparate_impact_ratio` use base rates from `y_true` rather than model selections.
- Use `prot_attr=["sex", "race"]` and tuple `priv_group` values when the task needs intersectional groups.

### Generic differences and ratios

Use `difference` and `ratio` to apply a sklearn metric by protected group.

```python
from sklearn.metrics import precision_score
from aif360.sklearn.metrics import difference, ratio

precision_gap = difference(
    precision_score,
    y_true, y_pred,
    prot_attr="sex", priv_group="Male", pos_label=1, zero_division=0,
)
precision_ratio = ratio(
    precision_score,
    y_true, y_pred,
    prot_attr="sex", priv_group="Male", pos_label=1, zero_division=0,
)
```

### Model-selection scorers

`make_scorer` converts AIF360 difference or ratio metrics into sklearn-compatible scorers.

```python
from sklearn.model_selection import GridSearchCV
from aif360.sklearn.metrics import make_scorer, statistical_parity_difference, disparate_impact_ratio

stat_parity_scorer = make_scorer(
    statistical_parity_difference,
    prot_attr="sex", priv_group="Male", pos_label=1,
)
di_scorer = make_scorer(
    disparate_impact_ratio,
    is_ratio=True,
    prot_attr="sex", priv_group="Male", pos_label=1, zero_division=0,
)

search = GridSearchCV(
    estimator,
    param_grid,
    scoring={"accuracy": "accuracy", "stat_parity": stat_parity_scorer, "di": di_scorer},
    refit="accuracy",
)
```

For difference metrics, the scorer returns negative absolute disparity. For ratio metrics with `is_ratio=True`, it returns `min(ratio, 1 / ratio)`.

### Individual, MDSS score, and optional OT metrics

```python
from aif360.sklearn.metrics import consistency_score, mdss_bias_score

consistency = consistency_score(X_numeric, y_pred, n_neighbors=5)
score = mdss_bias_score(y_true, probas_pred, X=None, subset=None, pos_label=1)
```

- `consistency_score` is feature-neighborhood based and does not compare privileged/unprivileged groups.
- `mdss_bias_score` scores a specified subset or the full data. For subgroup discovery (`MDSS_bias_scan`) and FACTS recourse details, use the sibling `detectors-and-explainers` sub-skill.
- `ot_distance` is optional and requires the `OptimalTransport` extra. Treat it as unverified until POT is installed and a tiny call passes.

## Estimator and meta-estimator patterns

### Reweighing

`Reweighing` computes new sample weights and intentionally breaks ordinary transformer expectations. Use it manually or through `ReweighingMeta`.

```python
from sklearn.linear_model import LogisticRegression
from aif360.sklearn.preprocessing import Reweighing, ReweighingMeta

rew = Reweighing(prot_attr="sex")
X_same, new_weight = rew.fit_transform(X_train, y_train, sample_weight=sample_weight)
clf = LogisticRegression(solver="liblinear").fit(X_same, y_train, sample_weight=new_weight)

wrapped = ReweighingMeta(
    LogisticRegression(solver="liblinear"),
    Reweighing(prot_attr="sex"),
).fit(X_train, y_train, sample_weight=sample_weight)
```

`ReweighingMeta` requires the wrapped estimator to accept `sample_weight` in `fit`.

### Preprocessing and inprocessing estimators

Extra-gated estimators follow sklearn `fit`/`predict`/`transform` patterns only after the matching extras are installed. See [optional estimators](optional-estimators.md) before using `LearnedFairRepresentations`, `FairAdapt`, `AdversarialDebiasing`, `ExponentiatedGradientReduction`, `GridSearchReduction`, `SenSeI`, or `SenSR`.

### Postprocessing with held-out validation

Postprocessors consume model scores or probabilities. `PostProcessingMeta` wraps a base estimator plus postprocessor and splits the training data so the postprocessor is fit on held-out predictions.

```python
from sklearn.linear_model import LogisticRegression
from aif360.sklearn.postprocessing import (
    CalibratedEqualizedOdds,
    RejectOptionClassifierCV,
    PostProcessingMeta,
)

pp = PostProcessingMeta(
    estimator=LogisticRegression(solver="liblinear"),
    postprocessor=RejectOptionClassifierCV("sex", scoring="disparate_impact", step=0.05),
    val_size=0.25,
    random_state=123,
)
pp.fit(X_train, y_train, sample_weight=sample_weight)
y_post = pp.predict(X_test)
```

Use `CalibratedEqualizedOdds("sex", cost_constraint="weighted")` when the task asks for calibrated equalized odds. Use `RejectOptionClassifierCV` when the task asks to search threshold/margin trade-offs.

Postprocessing caveats:

- `CalibratedEqualizedOdds`, `RejectOptionClassifier`, and `RejectOptionClassifierCV` are binary-classification postprocessors.
- They require probability estimates; wrapped base estimators must implement `predict_proba` when `PostProcessingMeta` sees a `requires_proba` postprocessor.
- If an sklearn `Pipeline` is required, put the whole preprocessing/model pipeline inside `PostProcessingMeta`, not `PostProcessingMeta` inside a pipeline step.
- For a prefit estimator, pass `prefit=True` and fit the postprocessor on data not used to train the estimator.

## Bundled smoke check

From this sub-skill directory:

```bash
python scripts/sklearn_metric_smoke.py --help
python scripts/sklearn_metric_smoke.py
```

The smoke uses an in-memory DataFrame/Series with protected attributes in a pandas index and does not call fetchers or networked data loaders.
