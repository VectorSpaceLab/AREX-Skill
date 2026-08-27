# Supervised Orange3 API reference

This reference is self-contained operating guidance for Orange3 supervised modeling. API facts were checked against the installed Orange3 package version `3.41.0.dev` and distilled from the supervised learning, modeling, evaluation, and widget modules.

## Core learner/model contract

### `Orange.base.Learner`

- `learner(data, progress_callback=None)` fits on an `Orange.data.Table` or one `Instance` coerced to a table and returns an `Orange.base.Model`.
- Before fitting, `Learner.__call__` runs `learner.incompatibility_reason(data.domain)` and raises `ValueError(reason)` if the domain is unsuitable.
- It applies active preprocessors, fits, attaches `domain`, `original_domain`, `original_data`, `supports_multiclass`, `name`, and `used_vals` to the model, then returns it.
- `learner.fit(X, Y, W=None)` is the matrix-level fit hook; `learner.fit_storage(data)` is the table-level fit hook. Subclasses implement one of these.
- `learner.preprocessors` and `learner.use_default_preprocessors` determine whether custom preprocessors replace or augment defaults. For `SklLearner`, defaults include class filtering, continuization, removal of all-NaN columns, and imputation.

### `Orange.base.Model`

- `model(data, ret=Model.Value)` predicts on a `Table`, `Instance`, NumPy array, SciPy CSR sparse matrix, or list/tuple rows.
- Return selectors:
  - `Model.Value` / `0`: predicted target values.
  - `Model.Probs` / `1`: classification probabilities.
  - `Model.ValueProbs` / `2`: `(values, probabilities)` for classification.
- Classification prediction shapes verified on a 3-class table: values `(n_rows,)`, probabilities `(n_rows, n_classes)`, single-row value scalar, single-row probabilities `(n_classes,)`.
- Regression models return values only; requesting probabilities on a continuous target raises `ValueError: cannot predict continuous distributions`.
- When called with a `Table`, the model attempts to transform data to the model domain. A class-variable name mismatch raises `DomainTransformationError`, for example when a model for target `iris` is asked to predict target `different`.
- A no-target prediction table can be valid if its feature domain can transform to the model domain; do not confuse this with no target in training data.

## Target adequacy

| Situation | Classification learner | Regression learner | Typical fix |
| --- | --- | --- | --- |
| No target or wrong target type | `Categorical class variable expected.` | `Numeric target variable expected.` | Assign one target with the correct type before fitting. |
| Multiple targets | `Too many target variables.` unless a rare learner supports multiclass/multitarget | `Too many target variables.` | Select one target variable for ordinary supervised evaluation. |
| Single class value | Many non-baseline learners fail during fitting; `MajorityLearner` can fit a constant model | Not applicable as a class-count issue, but degenerate numeric targets may score poorly | Add target diversity or use a constant/mean baseline intentionally. |
| Zero features | Fit/preprocess can fail, e.g. imputation requires at least one feature | Same | Add at least one feature or use a baseline learner that does not require features. |

## Classification APIs

Use `Orange.classification` for categorical targets. The namespace exports base aliases plus common learners, including:

- Baselines: `MajorityLearner`, `ThresholdLearner`, `CalibratedLearner`.
- Linear/probabilistic: `LogisticRegressionLearner`, `SoftmaxRegressionLearner`, `SGDClassificationLearner`, `NaiveBayesLearner`.
- Trees/ensembles/rules: `TreeLearner`, `SklTreeLearner`, `SimpleTreeLearner`, `RandomForestLearner`, `SimpleRandomForestLearner`, `GBClassifier`, `CN2Learner`, `CN2UnorderedLearner`, scoring-sheet learners.
- Neighbors/SVM/NN: `KNNLearner`, `SVMLearner`, `LinearSVMLearner`, `NuSVMLearner`, `NNClassificationLearner`.
- Optional wrappers can appear when dependencies import successfully, such as CatBoost and XGBoost classifiers.

Useful signatures verified live:

```python
Orange.classification.LogisticRegressionLearner(
    penalty='l2', dual=False, tol=0.0001, C=1.0,
    fit_intercept=True, intercept_scaling=1, class_weight=None,
    random_state=None, solver='auto', max_iter=100,
    verbose=0, n_jobs=1, preprocessors=None)

Orange.classification.RandomForestLearner(
    n_estimators=10, criterion='gini', max_depth=None,
    min_samples_split=2, min_samples_leaf=1,
    min_weight_fraction_leaf=0.0, max_features='sqrt',
    max_leaf_nodes=None, bootstrap=True, oob_score=False,
    n_jobs=1, random_state=None, verbose=0,
    class_weight=None, preprocessors=None)
```

`ModelClassification.predict_proba(data)` is a convenience wrapper around `model(data, ret=Model.Probs)`.

## Regression APIs

Use `Orange.regression` for continuous targets. The namespace exports base aliases plus common learners, including:

- Baselines/linear: `MeanLearner`, `LinearRegressionLearner`, `RidgeRegressionLearner`, `LassoRegressionLearner`, `ElasticNetLearner`, `ElasticNetCVLearner`, `SGDRegressionLearner`, `PolynomialLearner`.
- Trees/ensembles: `TreeLearner`, `SklTreeRegressionLearner`, `RandomForestRegressionLearner`, `SimpleRandomForestLearner`, `GBRegressor`.
- Neighbors/SVM/NN: `KNNRegressionLearner`, `SVRLearner`, `LinearSVRLearner`, `NuSVRLearner`, `NNRegressionLearner`.
- Specialized: `PLSRegressionLearner`, `CurveFitLearner`, optional CatBoost and XGBoost regressors when imports succeed.

Useful signatures verified live:

```python
Orange.regression.LinearRegressionLearner(
    preprocessors=None, fit_intercept=True)

Orange.regression.RandomForestRegressionLearner(
    n_estimators=10, criterion='squared_error', max_depth=None,
    min_samples_split=2, min_samples_leaf=1,
    min_weight_fraction_leaf=0.0, max_features=1.0,
    max_leaf_nodes=None, bootstrap=True, oob_score=False,
    n_jobs=1, random_state=None, verbose=0,
    preprocessors=None)
```

## `Orange.modelling` fitters

`Orange.modelling.Fitter` is a dispatching learner. A fitter infers the problem type from `Table.domain` or `Domain` and constructs the classification or regression learner listed in its `__fits__` map. Use it when widget or API code should accept either categorical or continuous targets.

Key behavior:

- `fitter.get_learner(data_or_domain_or_problem_type)` returns the underlying learner.
- `fitter(data)` fits through the dispatched learner and returns that learner's model.
- If the inferred type is neither `classification` nor `regression`, it raises `TypeError("No learner to handle ...")`.
- A fitter itself has no `params`; use `fitter.get_params(problem_type)`.

Common fitter dispatches verified live:

| Fitter | Classification dispatch | Regression dispatch |
| --- | --- | --- |
| `ConstantLearner` | `Orange.classification.MajorityLearner` | `Orange.regression.MeanLearner` |
| `RandomForestLearner` | `Orange.classification.RandomForestLearner` | `Orange.regression.RandomForestRegressionLearner` |
| `TreeLearner` | `Orange.classification.TreeLearner` | `Orange.regression.TreeLearner` |
| `KNNLearner` | `Orange.classification.KNNLearner` | `Orange.regression.KNNRegressionLearner` |
| `SVMLearner` | `Orange.classification.SVMLearner` | `Orange.regression.SVRLearner` |
| `GBLearner` | `Orange.classification.GBClassifier` | `Orange.regression.GBRegressor` |
| `SGDLearner` | `Orange.classification.SGDClassificationLearner` | `Orange.regression.SGDRegressionLearner` |

Other modelling fitters include AdaBoost, neural network, linear SVM, NuSVM, CatBoost, and XGBoost variants when their modules are available.

## Evaluation APIs

Import from either `Orange.evaluation` or `Orange.evaluation.scoring` depending on style.

### Validation methods

- `CrossValidation(k=10, stratified=True, random_state=0, store_data=False, store_models=False, warnings=None)` performs k-fold CV. For discrete classes and `stratified=True`, it tries stratified folds and records a warning if it must fall back.
- `ShuffleSplit(n_resamples=10, train_size=None, test_size=0.1, stratified=True, random_state=0, store_data=False, store_models=False)` performs repeated train/test splits.
- `LeaveOneOut()` tests each instance once.
- `TestOnTestData()(train_data, test_data, learners)` evaluates learners on separate test data.
- `TestOnTrainingData()(data, learners)` evaluates learners on their training data; use for diagnostics, not unbiased performance estimates.

Modern explicit style:

```python
results = Orange.evaluation.CrossValidation(k=5)(data, learners)
results = Orange.evaluation.TestOnTestData()(train, test, learners)
```

The constructor-call shorthand remains supported by `__new__`, for example `Orange.evaluation.CrossValidation(data, learners, k=5)`.

### `Results`

A `Results` object stores:

- `actual`: true target values for tested rows.
- `predicted`: shape `(n_learners, n_test_rows)`.
- `probabilities`: shape `(n_learners, n_test_rows, n_classes)` for classification; `None` for regression.
- `row_indices`, `folds`, `domain`, `learner_names`, `failed`, `train_time`, `test_time`.
- `models` only when validation was created with `store_models=True`; shape is usually `(n_folds, n_learners)`.
- `data` only when `store_data=True`.

By default, evaluation catches learner/model exceptions and stores them in `results.failed[learner_index]`. Pass `suppresses_exceptions=False` to the validation call to raise the original exception while debugging.

### Score families

Classification-compatible score classes require a discrete target:

- `CA` classification accuracy.
- `AUC` area under ROC; for multiclass it averages one-vs-rest AUCs, and it raises if the class variable has fewer than two values.
- `Precision`, `Recall`, `F1` accept target/average options through their call. Multiclass binary averaging requires choosing a target or a non-binary average.
- `LogLoss`, `Specificity`, `MatthewsCorrCoefficient`, and related registered score classes may be available.

Regression-compatible score classes require a continuous target:

- `MSE`, `RMSE`, `MAE`, `MAPE`, `SMAPE`, `R2`, `CVRMSE`.
- `MAPE` returns infinity if any actual value is zero; `CVRMSE` raises if the mean target is too small.

Score objects can be called as classes:

```python
accuracy = Orange.evaluation.CA(results)
rmse = Orange.evaluation.RMSE(results)
```

## Supervised widget API surfaces

Model widgets derive from the learner-widget base and generally have:

- Inputs: `Data`, `Preprocessor`.
- Outputs: `Learner`; `Model` when data is connected and valid.
- Extra outputs on some widgets, e.g. `Coefficients` for Logistic Regression and Linear Regression, `Support Vectors` for SVM.

Important model widgets include Constant, Logistic Regression, Naive Bayes, Tree, Random Forest, KNN, SVM, SGD, Neural Network, Gradient Boosting, AdaBoost, Calibrated Learner, Linear Regression, PLS, Curve Fit, Stacking, Load Model, and Save Model.

Evaluation widgets in scope:

| Widget | Main inputs | Main outputs | Notes |
| --- | --- | --- | --- |
| Test and Score | Data, Test Data, Learner(s), Preprocessor | Predictions table, Evaluation Results | Runs cross-validation, train/test, leave-one-out, or feature-defined folds. |
| Predictions | Data, Predictor model(s) | Selected Predictions, Predictions, Evaluation Results | Applies fitted models to data; can show model/domain mismatches. |
| Confusion Matrix | Evaluation Results | Selected Data, Annotated Data | Classification only. |
| ROC Analysis, Calibration Plot, Lift Curve | Evaluation Results | Calibrated Model where supported | Classification/probability workflows. |
| Parameter Fitter | Data, Learner | Interactive tuning output/state | Requires enough instances and compatible learner parameters. |
| Permutation Plot | Data, Learner | Plot/state | Requires enough instances and compatible learner/domain. |
| Feature as Predictor | Data | Learner, Model | Builds a `ColumnLearner`/`ColumnModel` from an existing variable. |

Widget validation mirrors API rules: one target, non-empty data, at least one feature, target diversity for most models, sparse support only for widgets/learners that declare it, and compatible train/test domains.
