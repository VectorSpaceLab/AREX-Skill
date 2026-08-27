# Supervised modeling troubleshooting

Use this guide when supervised Orange3 fitting, prediction, scoring, or model/evaluate widgets fail. Start with the target/domain checks, then inspect learner-specific failures and `Results.failed`.

## Quick diagnostic checklist

```python
print(data.domain)
print("rows", len(data), "X shape", data.X.shape, "Y shape", data.Y.shape)
print("class_vars", data.domain.class_vars)
print("has_discrete_class", data.domain.has_discrete_class)
print("has_continuous_class", data.domain.has_continuous_class)
print("sparse", data.is_sparse())
```

Then verify:

1. Exactly one target variable for ordinary supervised learners/evaluation.
2. Discrete target for `Orange.classification.*`; continuous target for `Orange.regression.*`.
3. At least one row, at least one feature, and enough defined target values.
4. Enough target diversity for the selected learner and score.
5. Train/test domains can transform to the fitted model domain.
6. `results.failed` is empty before interpreting score arrays.

## Missing target variable

Symptoms:

- Classification learner raises `ValueError: Categorical class variable expected.`
- Regression learner raises `ValueError: Numeric target variable expected.`
- Model widgets show `Data has no target variable. Select one with the Select Columns widget.`
- Parameter/evaluation widgets may show `Data has no target.`

Causes:

- The table has only attributes/metas and no `domain.class_var`.
- A data-preparation step moved the target into metas or attributes.
- A test/prediction table intentionally lacks a target; that can be OK for prediction but not for training/scoring.

Recovery:

- Use a data-preparation workflow to set one variable as target before fitting.
- For classification, choose a discrete target; for regression, choose a continuous target.
- For raw prediction with a fitted model, a no-target table may be acceptable if features can transform to the model domain. For evaluation/scoring, provide actual targets.

## Multiple targets

Symptoms:

- Learners raise `Too many target variables.`
- Model widgets show `Data contains multiple target variables. Select a single one with the Select Columns widget.`
- Evaluation may store `ValueError("Multiple targets are not supported.")` in `results.failed`.

Causes:

- `len(data.domain.class_vars) > 1` on a learner that does not set `supports_multiclass`.
- Ordinary `Orange.evaluation` supervised scoring expects one target column.

Recovery:

- Select one target before learner/evaluation widgets or API fitting.
- If you truly need multitarget behavior, verify the specific learner advertises support and do not assume Orange's standard evaluation/scoring widgets handle it.

## Sparse data

Symptoms:

- A widget shows `Sparse data is not supported.`
- A wrapped sklearn learner or preprocessing step fails while fitting sparse input.
- Sparse tables predict correctly for some models but fail for others.

Facts:

- `Orange.base.Model.__call__` accepts SciPy sparse input and converts sparse arrays to CSR for prediction.
- Many `SklLearner` pipelines can fit sparse tables, but support is learner/preprocessor-dependent.
- Learner widgets have a `supports_sparse` flag; widget validation can reject sparse data before fitting.

Recovery:

- Check `data.is_sparse()` and the chosen widget/learner support.
- Try a learner known to handle sparse input, or densify/reduce features upstream when memory permits.
- If a custom preprocessor is supplied, remember it may replace the learner defaults; make sure it handles sparse matrices.

## Fitting failures

Symptoms:

- API fitting raises a learner/sklearn exception.
- `Orange.evaluation` returns scores for some learners but `results.failed[i]` contains an exception for others.
- Model widgets show `Fitting failed.` or a learner-specific error.

Common causes:

- Wrong target type, multiple targets, no features, empty data, or all-missing targets.
- Incompatible learner parameters, e.g. invalid penalty/loss/kernel options.
- Dependency-specific warnings or errors from sklearn, CatBoost, or XGBoost wrappers.
- Non-convergence for iterative learners such as logistic regression, SGD, or neural networks.

Recovery:

```python
results = Orange.evaluation.CrossValidation(k=5)(data, learners)
for i, failure in enumerate(results.failed):
    if failure:
        print(i, type(failure).__name__, failure)

# Debug one failing learner by raising immediately:
Orange.evaluation.CrossValidation(k=5)(
    data, [learners[i]], suppresses_exceptions=False)
```

Then fix the root cause: adjust domain, add features/rows, choose a baseline, simplify parameters, increase `max_iter`, scale/normalize data, or switch to a learner compatible with the table.

## Single-class targets

Symptoms:

- `LogisticRegressionLearner` and many classifiers fail with sklearn errors like needing samples of at least two classes.
- `AUC` raises `Class variable has less than two values`.
- `Test and Score` widget reports `Target variable has only one value.` or a train-data error.
- Some baselines, especially `MajorityLearner`/`ConstantLearner`, can still fit a constant model.

Recovery:

- Check both declared class values and observed target values after filtering/missing-value removal.
- Add or restore examples from at least two classes before evaluating classifiers or class-probability metrics.
- Use `MajorityLearner` or `Orange.modelling.ConstantLearner` only when a constant baseline is intentionally acceptable.
- Avoid AUC/precision/recall/F1 interpretations until at least two classes appear in the evaluated data.

## Incompatible test data or prediction data

Symptoms:

- `DomainTransformationError`, e.g. `Model for 'iris' cannot predict 'different'`.
- `Test and Score` shows a test-data-incompatible error.
- `Predictions` warns about wrong targets or displays missing/NaN prediction cells for one model.

Causes:

- Test target name or variable definition differs from the model target.
- Feature variables have the same names but incompatible definitions or value sets.
- Test data has too few usable feature values after domain transformation.

Recovery:

- Align train and test domains before fitting/evaluation. Use the same target variable name and compatible value definitions.
- If only raw prediction is needed, test data may omit the target, but it still needs transformable feature variables.
- When mixing models in `Predictions`, verify all fitted models target the same problem.

## Empty data and empty results

Symptoms:

- Learners/evaluation raise `Test fold is empty`, `Train dataset is empty`, or `Dataset is empty`.
- `Confusion Matrix`, `Calibration Plot`, or related widgets show `Empty result on input. Nothing to display.`
- `Predictions` emits an empty evaluation result when all target values are unknown.

Causes:

- The input table has zero rows.
- Filtering or missing-target removal removed all rows.
- Cross-validation or feature-defined folds produce empty train/test subsets.
- Downstream evaluation widgets receive `Results` with no valid rows for their target/score type.

Recovery:

- Check `len(data)` after every filtering/preprocessing step.
- Reduce `k` for cross-validation or choose shuffle/train-test splitting when classes are rare.
- For `CrossValidationFeature`, choose a fold feature with at least two distinct values that each leave train and test rows.
- Feed classification-only widgets only classification `Results`; use regression-compatible scoring for continuous targets.

## Evaluation-memory errors

Symptoms:

- `Test and Score` widget shows `Out of memory`/memory error while producing predictions or augmented results.
- Large `Results` objects become expensive when storing data/models/probabilities for many learners, rows, folds, or classes.

Causes:

- `store_data=True` or `store_models=True` on large validation runs.
- Too many folds/resamples, learners, classes, or output tables.
- Downstream widgets request augmented data/predictions for a large evaluation result.

Recovery:

- Keep `store_data=False` and `store_models=False` unless needed.
- Reduce folds/resamples, number of learners, or data rows during debugging.
- Prefer scalar scores first; generate augmented Predictions tables only after choosing a smaller model set.
- If using widgets, disconnect heavy downstream consumers, rerun Test and Score, then reconnect selectively.

## Score-specific issues

- AUC needs a discrete target with at least two class values and probabilities. For multiclass, choose a target where required or use the default weighted one-vs-rest behavior.
- Precision/Recall/F1 with binary averaging on multiclass data requires specifying a target or using `average='weighted'`, `'macro'`, or `'micro'`.
- Regression percentage scores can be undefined or infinite when actual targets contain zeros; prefer RMSE/MAE/R2 first.
- Always inspect `results.failed` before trusting score arrays. A failed learner can leave no meaningful score for that learner.

## Widget-specific recovery map

| Widget family | Common warning/error | Recovery |
| --- | --- | --- |
| Model widgets | no target, multiple targets, single target value, no features, sparse unsupported, fitting failed | Fix domain with data-preparation widgets; choose compatible learner; add rows/features; avoid unsupported sparse input. |
| Test and Score | train-data error, incompatible test data, memory error, empty results | Validate train/test domains; reduce folds/models/data; inspect learner failures; feed one target only. |
| Predictions | wrong targets, missing predictions, empty evaluation output | Use fitted models for the same target; provide transformable feature variables; provide actual targets only when scoring is required. |
| Confusion/ROC/Calibration/Lift | regression input, invalid/empty values, no valid target class | Feed classification `Evaluation Results` with valid probabilities and at least two target classes. |
| Parameter Fitter/Permutation Plot | missing target, incompatible learner, not enough data, no parameters | Use a learner with tunable fitted parameters, enough rows, one target, and a compatible domain. |
