# sklearn API Reference

These signatures were confirmed from installed `aif360==0.6.1` package inspection. The base CPU environment verified imports for the package and sklearn metrics; extra-gated estimator workflows and `ot_distance` are optional/unverified until their matching extras are installed.

## Data model

`aif360.sklearn` expects tabular data as pandas objects:

- `X`: `pandas.DataFrame` of features.
- `y`: `pandas.Series` or `pandas.DataFrame` of targets.
- `sample_weight`: optional `pandas.Series` or array-like.
- Protected attributes are usually index levels on both `X` and `y`; use `prot_attr` to select one label, multiple labels, explicit arrays, or all index levels when `prot_attr=None`.

`standardize_dataset` returns a namedtuple with `X` and `y`, or `X`, `y`, and `sample_weight` when a weight column/array is supplied. Its filtering order is `usecols` -> `dropcols` -> `numeric_only` -> `dropna`.

## Dataset functions

### Standardizer

- `standardize_dataset(df, *, prot_attr, target, sample_weight=None, usecols=None, dropcols=None, numeric_only=False, dropna=True)`
  - Copies protected attributes into the index even when they are not kept as feature columns.
  - Drops target columns from features when target labels come from columns.
  - With `numeric_only=True`, non-numeric features are dropped; non-numeric protected attributes or targets can emit `NumericConversionWarning`.

### Fetchers and cache/network caveats

- `fetch_adult(subset='all', *, data_home=None, cache=True, binary_race=True, usecols=None, dropcols=None, numeric_only=False, dropna=True)`
  - `subset` is `train`, `test`, or `all`.
  - First use can download from OpenML unless data are already cached. The Adult fetcher returns `X`, `y`, and `sample_weight`.
  - Protected attributes are race and sex. `binary_race=True` collapses non-white categories for the protected index.

- `fetch_german(*, data_home=None, cache=True, binary_age=True, usecols=None, dropcols=None, numeric_only=False, dropna=True)`
  - First use can download from OpenML unless data are already cached.
  - Protected attributes include sex, age, and foreign worker. `binary_age=True` bins age while retaining the continuous age feature unless dropped.

- `fetch_bank(*, data_home=None, cache=True, binary_age=True, percent10=False, usecols=None, dropcols=['duration'], numeric_only=False, dropna=False)`
  - First use can download from OpenML unless data are already cached.
  - `percent10=True` chooses the reduced dataset. `dropna=False` is the default for this loader.
  - The default drops `duration` because it is often a leakage-prone feature in bank-marketing workflows.

- `fetch_compas(subset='all', *, data_home=None, cache=True, binary_race=False, usecols=['sex', 'age', 'age_cat', 'race', 'juv_fel_count', 'juv_misd_count', 'juv_other_count', 'priors_count', 'c_charge_degree', 'c_charge_desc'], dropcols=None, numeric_only=False, dropna=True)`
  - `subset` is `all` or `violent`.
  - First use can download a public CSV unless cached. `binary_race=True` keeps only the binary race grouping used by the loader.
  - Sex is ordered with Female as privileged and Male as unprivileged in this loader; do not assume the same numeric convention as other datasets.

- `fetch_meps(panel, *, accept_terms=None, data_home=None, cache=True, usecols=['REGION', 'AGE', 'SEX', 'RACE', 'MARRY', 'FTSTU', 'ACTDTY', 'HONRDC', 'RTHLTH', 'MNHLTH', 'HIBPDX', 'CHDDX', 'ANGIDX', 'MIDX', 'OHRTDX', 'STRKDX', 'EMPHDX', 'CHBRON', 'CHOLDX', 'CANCERDX', 'DIABDX', 'JTPAIN', 'ARTHDX', 'ARTHTYPE', 'ASTHDX', 'ADHDADDX', 'PREGNT', 'WLKLIM', 'ACTLIM', 'SOCLIM', 'COGLIM', 'DFHEAR42', 'DFSEE42', 'ADSMOK42', 'PCS42', 'MCS42', 'K6SUM42', 'PHQ242', 'EMPST', 'POVCAT', 'INSCOV'], dropcols=None, numeric_only=False, dropna=True)`
  - `panel` must be `19`, `20`, or `21`.
  - First use can download MEPS data and can prompt for terms unless `accept_terms=True` is supplied. Only set `accept_terms=True` when the caller accepts the data terms.
  - Returns `X`, `y`, and `sample_weight`.

- `fetch_lawschool_gpa(subset='all', *, data_home=None, cache=True, binary_race=True, fillna_gender='female', usecols=['race', 'gender', 'lsat', 'ugpa'], dropcols=None, numeric_only=False, dropna=True)`
  - `subset` is `train`, `test`, or `all`.
  - First use can download a SAS data file unless cached.
  - This is a regression dataset: the target is standardized first-year GPA rather than a binary class label.

## Metric functions

### Meta-metrics and scorer factory

- `difference(func, y_true, y_pred=None, prot_attr=None, priv_group=1, sample_weight=None, **kwargs)`
  - Computes unprivileged minus privileged value for any compatible metric function.
  - If `prot_attr=None`, all protected index levels are used.

- `ratio(func, y_true, y_pred=None, prot_attr=None, priv_group=1, sample_weight=None, zero_division='warn', **kwargs)`
  - Computes unprivileged divided by privileged value for any compatible metric function.
  - Use `zero_division=0` or `1` when a group can have zero denominator.

- `make_scorer(score_func, is_ratio=False, **kwargs)`
  - Wraps AIF360 difference/ratio metrics for sklearn model selection.
  - For difference metrics, the scorer optimizes negative absolute disparity. For ratio metrics, pass `is_ratio=True`; the scorer optimizes `min(ratio, 1/ratio)`.

### Group fairness metrics

- `statistical_parity_difference(y_true, y_pred=None, *, prot_attr=None, priv_group=1, pos_label=1, sample_weight=None)`
  - With only `y_true`, computes base-rate difference. With `y_pred`, computes selection-rate difference.

- `disparate_impact_ratio(y_true, y_pred=None, *, prot_attr=None, priv_group=1, pos_label=1, sample_weight=None, zero_division='warn')`
  - With only `y_true`, computes base-rate ratio. With `y_pred`, computes selection-rate ratio.

- `equal_opportunity_difference(y_true, y_pred, *, prot_attr=None, priv_group=1, pos_label=1, sample_weight=None)`
  - Difference in recall/TPR between unprivileged and privileged groups.

- `average_odds_difference(y_true, y_pred, *, prot_attr=None, priv_group=1, pos_label=1, sample_weight=None)`
  - Average of FPR difference and TPR difference; optimal value is zero.

- `average_odds_error(y_true, y_pred, *, prot_attr=None, priv_group=None, pos_label=1, sample_weight=None)`
  - Average absolute FPR/TPR disparity; if `priv_group=None`, the selected protected attribute must be binary.

- `mdss_bias_score(y_true, probas_pred, X=None, subset=None, *, pos_label=1, scoring='Bernoulli', overpredicted=True, penalty=1e-17, **kwargs)`
  - Scores a prespecified subset using MDSS scoring. For full subgroup discovery and FACTS workflows, hand off to the `detectors-and-explainers` sub-skill.

- `ot_distance(y_true: pandas.Series, y_pred: Union[pandas.Series, pandas.DataFrame], prot_attr: pandas.Series = None, pos_label: Union[str, float] = None, scoring: str = 'Wasserstein1', num_iters: int = 100000.0, penalty: float = 1e-17, mode: str = 'binary', cost_matrix: numpy.ndarray = None, **kwargs)`
  - Optional/unverified in the base environment. Requires the `OptimalTransport` extra, which provides POT as `ot`.
  - `mode='binary'` and `mode='continuous'` expect `y_pred` as a `Series`; `mode='nominal'` and `mode='ordinal'` expect a `DataFrame` with one prediction column per class.

### Individual fairness metric

- `consistency_score(X, y, n_neighbors=5)`
  - KNN-based individual consistency score. It uses features and targets, not protected-index group comparison.

## Estimators and meta-estimators

### Preprocessing

- `Reweighing(prot_attr=None)`
  - Base-supported. `fit_transform(X, y, sample_weight=None)` returns `(X, transformed_sample_weight)` and intentionally does not behave like a standard sklearn transformer.

- `ReweighingMeta(estimator, reweigher=None)`
  - Base-supported meta-estimator. Uses `Reweighing` to compute new sample weights before fitting an estimator that accepts `sample_weight`.

- `LearnedFairRepresentations(prot_attr=None, n_prototypes=5, reconstruct_weight=0.01, target_weight=1.0, fairness_weight=50.0, tol=0.0001, max_iter=200, verbose=0, random_state=None)`
  - Optional/unverified. Requires the `LFR` extra.

- `FairAdapt(prot_attr, adj_mat)`
  - Optional/unverified. Requires the `FairAdapt` extra and an R bridge/runtime. It expects a binary protected attribute and a causal adjacency matrix matching the train data columns.

### Inprocessing

- `AdversarialDebiasing(prot_attr=None, scope_name='classifier', adversary_loss_weight=0.1, num_epochs=50, batch_size=128, classifier_num_hidden_units=200, debias=True, verbose=False, random_state=None)`
  - Optional/unverified. Requires the `AdversarialDebiasing` extra and TensorFlow v1-compatible execution.

- `ExponentiatedGradientReduction(prot_attr, estimator, constraints, eps=0.01, max_iter=50, nu=None, eta0=2.0, run_linprog_step=True, drop_prot_attr=True)`
  - Optional/unverified. Requires the `Reductions` extra. Supported string constraints include demographic parity, equalized odds, true-positive-rate parity, false-positive-rate parity, and error-rate parity.

- `GridSearchReduction(prot_attr, estimator, constraints, constraint_weight=0.5, grid_size=10, grid_limit=2.0, grid=None, drop_prot_attr=True, loss='ZeroOne', min_val=None, max_val=None)`
  - Optional/unverified. Requires the `Reductions` extra. Supports classification and bounded-group-loss regression branches.

- `SenSeI(module, *, criterion, distance_x, distance_y, rho, eps, auditor_nsteps, auditor_lr, regression='auto', **kwargs)`
  - Optional/unverified. Requires the `inFairness` extra, a torch module, criterion, and inFairness distance objects.

- `SenSR(module, *, criterion, distance_x, eps, lr_lamb, lr_param, auditor_nsteps, auditor_lr, regression='auto', **kwargs)`
  - Optional/unverified. Requires the `inFairness` extra, a torch module, criterion, and inFairness distance objects.

### Postprocessing

- `CalibratedEqualizedOdds(prot_attr=None, cost_constraint='weighted', random_state=None)`
  - Base-supported. Binary classification only. Requires probability estimates as input or use through `PostProcessingMeta`.

- `RejectOptionClassifier(prot_attr=None, threshold=0.5, margin=0.1)`
  - Base-supported. Binary classification only. Expects one probability column per class and protected attributes in the prediction DataFrame index.

- `RejectOptionClassifierCV(prot_attr=None, *, scoring, step=0.05, refit=True, **kwargs)`
  - Base-supported grid search over `RejectOptionClassifier` thresholds and margins. Valid built-in scoring strings are `statistical_parity`, `average_odds`, `equal_opportunity`, and `disparate_impact`.

- `PostProcessingMeta(estimator, postprocessor, *, prefit=False, val_size=0.25, **options)`
  - Base-supported meta-estimator. Splits data to fit the base estimator and postprocessor without leakage, unless `prefit=True` is used.
