# Data-preparation troubleshooting

Use this guide when synthetic data, feature encoding, propensity estimation, matching, or balance reporting fails.

## Propensity model problems

### `ValueError` about one class, folds, or class imbalance

Cause: the treatment vector has only one arm in the current sample, or a cross-validation fold cannot contain both arms.

Fixes:

1. Check `df[treatment_col].value_counts(dropna=False)` before fitting.
2. Reduce `n_fold` for elastic-net propensity when the minority arm is small.
3. Fit within larger strata, or avoid group-level propensity fits for groups with only one arm.
4. For matching by group, keep propensity estimation global when group-specific samples are too small.

### Scores are nearly all `0` or `1`

Cause: separation, target leakage, overly predictive treatment-assignment variables, or a group with poor common support.

Fixes:

- Remove post-treatment or treatment-derived feature columns.
- Inspect feature importance or coefficients outside this sub-skill before trusting the score.
- Use `clip_bounds=(1e-3, 1 - 1e-3)` or a more conservative interval for downstream learners.
- Consider `GradientBoostedPropensityModel` only if its optional dependency imports cleanly and the sample is large enough.
- Run `create_table_one` before and after matching to verify actual balance improvements.

### `Failed to import duecredit` warning

This optional warning can appear during CausalML import. It does not by itself block propensity, matching, or synthetic-data workflows.

### XGBoost import or runtime errors

`GradientBoostedPropensityModel` requires XGBoost. If it is unavailable or incompatible, use `ElasticNetPropensityModel` for baseline propensity scores, or fix the optional dependency stack before choosing the gradient-boosted path.

## Common-support and caliper failures

### Matched output is empty or much smaller than expected

Likely causes:

- caliper too strict;
- no overlap between treated and control propensity distributions;
- group-stratified matching has small or one-sided groups;
- `ratio` is too high for available controls;
- `replace=False` exhausts the opposite-arm pool.

Fixes:

1. Compare score quantiles by treatment arm.
2. Start with `caliper=0.2`, then loosen or tighten based on balance and retention.
3. Try `replace=True` when control supply is scarce.
4. Use `ratio=1` first, then increase only if retention and balance are acceptable.
5. Remove or merge exact groups that lack both arms, if the study design permits.

### Multiple score columns fail with `replace=False`

This is an API constraint. Use exactly one score column for no-replacement matching, or set `replace=True` for multi-column neighbor matching.

### String or categorical matching columns cause errors

`NearestNeighborMatch` computes numeric distances. Encode categorical variables first, or use `match_by_group` for exact categorical stratification and match on a numeric score within each group.

## Balance-table problems

### `create_table_one` fails on strings or objects

The balance table computes means, standard deviations, and standardized mean differences. Provide numeric covariates only. For categorical balance, create indicator columns or inspect category proportions separately.

### SMD is `nan` or infinite

Likely causes include zero variance in one or both arms, all-missing values, or one arm absent after filtering.

Fixes:

- Verify both treatment groups remain after filtering and matching.
- Drop constant covariates from SMD review or audit them manually.
- Impute or remove missing values before balance calculations.

### Balance improves on propensity but worsens on key covariates

Propensity-only matching can miss individual covariate imbalance. Try multi-column matching with `replace=True`, add key covariates to `MatchOptimizer(matching_covariates=...)`, or enforce exact group matching for non-negotiable strata.

## Feature encoding and leakage problems

### Train/test category mappings differ

`load_data` fits encoders on every call. If train and scoring data must share category mappings, fit `LabelEncoder` or `OneHotEncoder` on train data and reuse the fitted encoder on scoring data.

### All categorical features disappear

Rare-level grouping can map all categories to the grouped label, and `OneHotEncoder` drops that grouped label from explicit dummy columns. Reduce `min_obs`, add numeric features, or treat the column as an exact group instead of one-hot encoding.

### Model seems too accurate or propensity has perfect AUC

Check for leakage. Remove outcome columns, true effects, generated probability columns, post-treatment variables, treatment flags, and assignment-rule columns from propensity and matching features unless the task is an oracle simulation.

## CSV helper problems

### Missing column errors

Check spelling and quoting in `--treatment-column`, `--feature-columns`, `--matching-covariates`, `--score-column`, and `--groupby-column`. Shells split on spaces, so pass column names containing spaces carefully or rename columns first.

### Score column exists but should be recomputed

Pass `--force-propensity` to overwrite the requested score column from `--feature-columns`.

### Feature columns are omitted while score must be computed

If the score column is absent, the helper needs `--feature-columns` to estimate it. Either provide feature columns or add a numeric score column to the input CSV.

### Treatment column contains strings

The helper requires binary values castable to integers `0` and `1`. Map labels such as `control` and `treated` to numeric values before running, or create a new binary treatment column.

### Group matching drops too many rows

Each exact group is matched separately. Inspect treatment counts by group and merge sparse strata, remove the groupby option, or loosen the caliper if the design allows it.

## Missing or moved APIs

- `make_uplift_regression` is not an importable CausalML 0.17.0 API from `causalml.dataset`. Use `synthetic_data(...)` for continuous-outcome synthetic examples.
- `FeatureEffectExplainer` is not available from `causalml.features` in CausalML 0.17.0. Route feature interpretation or feature-selection tasks to the analysis-and-decision sub-skill and use available classes there.
