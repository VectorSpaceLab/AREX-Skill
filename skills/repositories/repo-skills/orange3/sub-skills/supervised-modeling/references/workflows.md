# Supervised modeling workflows

These workflows assume an `Orange.data.Table` with one target variable. Use data-preparation guidance first if the table/domain itself must be loaded, cleaned, or reshaped.

## 1. Fit and predict a classifier

```python
import Orange
from Orange.base import Model

data = Orange.data.Table("iris")
learner = Orange.classification.LogisticRegressionLearner(max_iter=200)
model = learner(data)

values = model(data[:5], ret=Model.Value)
probabilities = model(data[:5], ret=Model.Probs)
values2, probabilities2 = model(data[:5], ret=Model.ValueProbs)
labels = data.domain.class_var.values
print([labels[int(v)] for v in values])
print(probabilities.shape)  # (n_rows, n_classes)
```

Checklist:

- `data.domain.has_discrete_class` must be true.
- For probability output, use a classifier that can supply probabilities or Orange can infer probabilities from returned class values.
- For a single instance, Orange returns a scalar value and a 1-D probability vector.

## 2. Fit and predict a regressor

```python
import Orange

data = Orange.data.Table("housing")
learner = Orange.regression.LinearRegressionLearner()
model = learner(data)

predicted = model(data[:5])
for yhat, row in zip(predicted, data[:5]):
    print(float(yhat), row.get_class())
```

Checklist:

- `data.domain.has_continuous_class` must be true.
- Use `ret=Model.Value` or omit `ret`; probability returns are classification-only.
- Baselines such as `MeanLearner` are useful for comparisons and degenerate data.

## 3. Dispatch with `Orange.modelling` fitters

Use fitters when a workflow should accept either classification or regression tables.

```python
import Orange

for data in [Orange.data.Table("iris"), Orange.data.Table("housing")]:
    fitter = Orange.modelling.RandomForestLearner(n_estimators=50, random_state=0)
    dispatched = fitter.get_learner(data)
    model = fitter(data)
    print(data.domain.class_var, type(dispatched).__name__, type(model).__name__)
```

Rules:

- A fitter infers `classification` from a discrete target and `regression` from a continuous target.
- Pass parameters that the selected underlying learner accepts; the fitter filters and may remap some keyword names.
- `fitter.params` is not available; call `fitter.get_params("classification")` or `fitter.get_params("regression")` after the relevant underlying learner is created.

## 4. Cross-validate classifiers

```python
import Orange

data = Orange.data.Table("iris")
learners = [
    Orange.classification.MajorityLearner(),
    Orange.classification.LogisticRegressionLearner(max_iter=200),
    Orange.classification.RandomForestLearner(n_estimators=50, random_state=0),
]
for learner in learners:
    learner.name = learner.name or type(learner).__name__

results = Orange.evaluation.CrossValidation(k=5, random_state=0)(data, learners)
ca = Orange.evaluation.CA(results)
auc = Orange.evaluation.AUC(results)

for i, learner in enumerate(learners):
    failed = results.failed[i]
    status = "ok" if not failed else f"failed: {type(failed).__name__}: {failed}"
    print(f"{learner.name:18s} CA={ca[i]:.3f} AUC={auc[i]:.3f} {status}")
```

Notes:

- `CrossValidation` expects a list of learners, not fitted models.
- For discrete targets, `results.probabilities` is populated with shape `(n_learners, n_rows, n_classes)` when probabilities are available.
- For debugging, rerun as `CrossValidation(k=5)(data, learners, suppresses_exceptions=False)` to raise the original learner exception.

## 5. Cross-validate regressors

```python
import Orange

data = Orange.data.Table("housing")
learners = [
    Orange.regression.MeanLearner(),
    Orange.regression.LinearRegressionLearner(),
    Orange.regression.RidgeRegressionLearner(),
    Orange.regression.RandomForestRegressionLearner(n_estimators=50, random_state=0),
]

results = Orange.evaluation.CrossValidation(k=5, random_state=0)(data, learners)
rmse = Orange.evaluation.RMSE(results)
r2 = Orange.evaluation.R2(results)

for i, learner in enumerate(learners):
    print(f"{learner.name:16s} RMSE={rmse[i]:.3f} R2={r2[i]:.3f}")
```

Notes:

- For continuous targets, `results.probabilities` is `None`.
- `RMSE`, `MSE`, `MAE`, and `R2` are safer first-pass regression scores than percentage scores on targets that may include zero.

## 6. Train/test evaluation

Use a separate test table when you have a genuine held-out set.

```python
import Orange

train = Orange.data.Table("iris")[:100]
test = Orange.data.Table("iris")[100:]
learners = [Orange.classification.TreeLearner(), Orange.classification.NaiveBayesLearner()]

results = Orange.evaluation.TestOnTestData()(train, test, learners)
print(Orange.evaluation.CA(results))
```

Compatibility checklist:

- Train and test targets must represent the same target variable.
- Test data with no target can be valid for raw model prediction, but supervised scoring needs actual targets.
- If target names/values conflict, Orange may raise `DomainTransformationError` or a widget may show an incompatible-test-data warning.

## 7. Use preprocessors with learners

```python
import Orange
from Orange.preprocess import Normalize

data = Orange.data.Table("iris")
learner = Orange.classification.LogisticRegressionLearner(
    preprocessors=[Normalize()]
)
model = learner(data)
```

Important distinction:

- Passing `preprocessors=[...]` to many learners replaces default learner preprocessors unless `use_default_preprocessors` is explicitly enabled.
- If you need Orange's default handling plus extra preprocessing, either use an upstream Orange preprocessing workflow or set `learner.use_default_preprocessors = True` after constructing the learner and before fitting.
- Model widgets that wrap `Orange.modelling.Fitter` set `use_default_preprocessors=True` for the dispatched fitter path.

## 8. Widget workflow: model, evaluate, inspect predictions

A typical Canvas supervised workflow is:

```text
File/Data Table
  -> Select Columns (ensure one target)
  -> one or more model widgets (Logistic Regression, Random Forest, Linear Regression, ...)
  -> Test and Score
  -> Predictions / Confusion Matrix / ROC Analysis / Calibration Plot / Lift Curve
```

Operational guidance:

- Model widgets output `Learner` immediately from settings and output `Model` only when connected data is valid.
- Use `Preprocess` input to inject a preprocessor pipeline; watch for the widget information message that defaults were replaced.
- `Test and Score` accepts multiple learner inputs and an optional Test Data input. Its `Evaluation Results` output feeds score/curve widgets.
- `Predictions` accepts fitted `Model` inputs. It can output annotated data and `Evaluation Results` for downstream evaluation widgets when actual targets are available.
- Confusion Matrix, ROC Analysis, Calibration Plot, and Lift Curve are classification-oriented; use regression scores/plots for continuous targets instead.

## 9. Minimal pre-fit validation helper pattern

This is a pattern to embed in user code, not a bundled script:

```python
def assert_supervised_ready(data, *, task):
    if len(data) == 0:
        raise ValueError("training data is empty")
    if len(data.domain.class_vars) != 1:
        raise ValueError("expected exactly one target variable")
    if task == "classification" and not data.domain.has_discrete_class:
        raise ValueError("expected a categorical target")
    if task == "regression" and not data.domain.has_continuous_class:
        raise ValueError("expected a numeric target")
    if data.X.size == 0:
        raise ValueError("expected at least one feature")
```

Do not overuse this helper: individual Orange learners may have additional requirements, such as minimum class counts, sparse support, or dependency-specific parameter limits.
