# Component contracts

This reference is the self-contained contract for adding custom auto-sklearn
components. It covers classifiers, regressors, feature preprocessors, and data
preprocessors without requiring access to the original repository.

## Import names and inspected version

- Python package import: `autosklearn`.
- Inspected version: `0.16.0dev` / `0.16.0.dev0`.
- Core extension imports:

```python
from ConfigSpace.configuration_space import ConfigurationSpace
from autosklearn.askl_typing import FEAT_TYPE_TYPE
from autosklearn.pipeline.components.base import (
    AutoSklearnClassificationAlgorithm,
    AutoSklearnRegressionAlgorithm,
    AutoSklearnPreprocessingAlgorithm,
)
from autosklearn.pipeline.constants import (
    DENSE, SPARSE, SIGNED_DATA, UNSIGNED_DATA, PREDICTIONS, INPUT,
)
```

## Base classes and required methods

| Kind | Base class | Required prediction/transform methods | Typical wrapped object attribute |
|---|---|---|---|
| Classifier | `AutoSklearnClassificationAlgorithm` | `fit(X, y)`, `predict(X)`, `predict_proba(X)` | `self.estimator` |
| Regressor | `AutoSklearnRegressionAlgorithm` | `fit(X, y)`, `predict(X)` | `self.estimator` |
| Feature preprocessor | `AutoSklearnPreprocessingAlgorithm` | `fit(X, y=None)`, `transform(X)` | `self.preprocessor` |
| Data preprocessor | `AutoSklearnPreprocessingAlgorithm` | `fit(X, y=None)`, `transform(X)` | custom or no-op; often no learned object |

All kinds also need these static methods:

```python
@staticmethod
def get_properties(dataset_properties=None):
    ...

@staticmethod
def get_hyperparameter_search_space(
    feat_type: FEAT_TYPE_TYPE | None = None,
    dataset_properties=None,
):
    ...
```

The base class `set_hyperparameters()` sets attributes from a sampled
ConfigSpace configuration. Therefore every hyperparameter name in the component
ConfigurationSpace must already exist as an instance attribute set by
`__init__`. Keep constructor parameters explicit and store all of them:

```python
def __init__(self, alpha=1.0, random_state=None):
    self.alpha = alpha
    self.random_state = random_state
    self.estimator = None
```

Convert ConfigSpace strings/numbers to the wrapped estimator's expected Python
types inside `fit()` before constructing the wrapped scikit-learn object.

## `get_properties()` exact key set

Registration validates the exact property key set. Include every key below and
no extras:

| Key | Meaning | Typical classifier value | Typical regressor value | Typical preprocessor value |
|---|---|---|---|---|
| `shortname` | Short display label | short string | short string | short string |
| `name` | Human-readable name | full string | full string | full string |
| `handles_regression` | Usable for regression tasks | `False` | `True` | depends |
| `handles_classification` | Usable for classification tasks | `True` | `False` | depends |
| `handles_multiclass` | Supports multiclass classification | depends | `False` | depends |
| `handles_multilabel` | Supports multilabel classification | depends | `False` | depends |
| `handles_multioutput` | Supports multioutput regression / outputs | usually `False` | depends | depends |
| `is_deterministic` | Same seed gives same result | depends | depends | depends |
| `input` | Tuple/list of accepted data properties | e.g. `(DENSE, SPARSE, UNSIGNED_DATA)` | e.g. `(DENSE, SPARSE, SIGNED_DATA, UNSIGNED_DATA)` | e.g. `(DENSE, UNSIGNED_DATA, SIGNED_DATA)` |
| `output` | Tuple/list of produced data properties | `(PREDICTIONS,)` | `(PREDICTIONS,)` | e.g. `(INPUT,)` or `(DENSE, SIGNED_DATA, UNSIGNED_DATA)` |

Use the constants from `autosklearn.pipeline.constants`:

- Data layout: `DENSE`, `SPARSE`.
- Value sign: `SIGNED_DATA`, `UNSIGNED_DATA`.
- Prediction output: `PREDICTIONS` for classifiers/regressors.
- Pass-through preprocessor output: `INPUT` if the transformer preserves the
  input layout/sign; otherwise state the produced layout/sign explicitly.

Registration rejects missing keys such as `handles_multioutput` and rejects
unknown keys. Sparse/dense and signed/unsigned values are used by pipeline
search-space compatibility logic. Do not claim `SPARSE` input unless the wrapped
estimator or transformer truly accepts sparse matrices; otherwise sparse data
can route into a component that later fails at fit time.

## ConfigSpace contract

Return a `ConfigSpace.configuration_space.ConfigurationSpace`. An empty space is
valid for a component with no tunable hyperparameters:

```python
from ConfigSpace.configuration_space import ConfigurationSpace

@staticmethod
def get_hyperparameter_search_space(feat_type=None, dataset_properties=None):
    return ConfigurationSpace()
```

Common hyperparameter pattern:

```python
from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import CategoricalHyperparameter, UniformFloatHyperparameter
from ConfigSpace.conditions import EqualsCondition

cs = ConfigurationSpace()
kernel = CategoricalHyperparameter("kernel", ["rbf", "poly"], default_value="rbf")
gamma = UniformFloatHyperparameter("gamma", lower=1e-5, upper=1.0, log=True, default_value=0.1)
degree = UniformFloatHyperparameter("degree", lower=2, upper=5, default_value=3)
cs.add_hyperparameters([kernel, gamma, degree])
cs.add_condition(EqualsCondition(degree, kernel, "poly"))
return cs
```

Rules:

- Every default value must be inside its domain and among categorical choices.
- Conditions must refer to hyperparameters already added to the configuration
  space.
- Conditional defaults should still be valid when the condition is active.
- Keep ranges narrow for expensive estimators; use the custom component wrapper
  as a way to restrict a broad built-in search space.
- Hyperparameter names become attributes on the component instance. If the
  sampled value is `"None"` or another sentinel, normalize it in `fit()`.

## Registration functions and component IDs

Register a custom class after it is defined and before constructing the
AutoSklearn estimator:

| Kind | Function | Include/exclude key | Custom component ID |
|---|---|---|---|
| Classifier | `autosklearn.pipeline.components.classification.add_classifier(MyClassifier)` | `"classifier"` | class name, e.g. `"MyClassifier"` |
| Regressor | `autosklearn.pipeline.components.regression.add_regressor(MyRegressor)` | `"regressor"` | class name |
| Feature preprocessor | `autosklearn.pipeline.components.feature_preprocessing.add_preprocessor(MyPreprocessor)` | `"feature_preprocessor"` | class name |
| Data preprocessor | `autosklearn.pipeline.components.data_preprocessing.add_preprocessor(MyDataPreprocessor)` | `"data_preprocessor"` | class name |

Registration uses a strict direct-base check: the object must be a class whose
immediate base is the expected base class. Passing an instance, a plain
scikit-learn estimator, the wrong base class, or a multi-level subclass can raise
`TypeError: add_component works only with a subclass of ...`.

Example classifier restriction:

```python
import autosklearn.classification
import autosklearn.pipeline.components.classification

autosklearn.pipeline.components.classification.add_classifier(MyClassifier)

automl = autosklearn.classification.AutoSklearnClassifier(
    include={"classifier": ["MyClassifier"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
```

The ID is not the `name` or `shortname` property and not the source filename; for
third-party components it is the Python class name stored in the registry.
Built-in component IDs are the catalog strings below.

## Built-in component IDs

Use these exact IDs for built-in components when restricting search. For ordinary
built-in include/exclude planning with budgets or Dask, route to the
search-and-parallelism sub-skill; this catalog is included here because custom
components often need to avoid collisions or replace a built-in component.

### Classifiers

`adaboost`, `bernoulli_nb`, `decision_tree`, `extra_trees`, `gaussian_nb`,
`gradient_boosting`, `k_nearest_neighbors`, `lda`, `liblinear_svc`, `libsvm_svc`,
`mlp`, `multinomial_nb`, `passive_aggressive`, `qda`, `random_forest`, `sgd`.

### Regressors

`adaboost`, `ard_regression`, `decision_tree`, `extra_trees`,
`gaussian_process`, `gradient_boosting`, `k_nearest_neighbors`, `liblinear_svr`,
`libsvm_svr`, `mlp`, `random_forest`, `sgd`.

### Feature preprocessors

`densifier`, `extra_trees_preproc_for_classification`,
`extra_trees_preproc_for_regression`, `fast_ica`, `feature_agglomeration`,
`kernel_pca`, `kitchen_sinks`, `liblinear_svc_preprocessor`, `no_preprocessing`,
`nystroem_sampler`, `pca`, `polynomial`, `random_trees_embedding`,
`select_percentile_classification`, `select_percentile_regression`,
`select_rates_classification`, `select_rates_regression`, `truncatedSVD`.

### Data preprocessors

`feature_type`.

## Include/exclude keys by pipeline step

- Classifier estimator: `include={"classifier": ["random_forest"]}` or custom
  `include={"classifier": ["MyClassifier"]}`.
- Regressor estimator: `include={"regressor": ["random_forest"]}` or custom
  `include={"regressor": ["MyRegressor"]}`.
- Feature preprocessor: `include={"feature_preprocessor": ["no_preprocessing"]}`
  or custom `include={"feature_preprocessor": ["MyPreprocessor"]}`.
- Data preprocessor: `include={"data_preprocessor": ["feature_type"]}` or custom
  `include={"data_preprocessor": ["MyDataPreprocessor"]}`.

Never set both `include` and `exclude` for the same estimator object; component
choice code raises a value error when both are provided.

## Search-space narrowing patterns

To narrow a built-in search space, write a custom wrapper around the same
underlying scikit-learn estimator but expose only the hyperparameters and ranges
you want auto-sklearn to tune. Then register the custom class and either include
it explicitly or exclude the built-in component ID. Example intent:

```python
# custom class exposes only n_estimators and max_features
add_classifier(CustomRandomForest)

automl = autosklearn.classification.AutoSklearnClassifier(
    exclude={"classifier": ["random_forest"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
```

For a strict custom-only search, prefer `include={"classifier": ["CustomRandomForest"]}`.
Use `exclude` when you want every other compatible classifier plus your custom
component except the built-in being replaced.

## Minimal no-training checks

Use these before any expensive fit:

```python
# 1. exact properties
props = MyComponent.get_properties()
assert set(props) == {
    "shortname", "name", "handles_regression", "handles_classification",
    "handles_multiclass", "handles_multilabel", "handles_multioutput",
    "is_deterministic", "input", "output",
}

# 2. ConfigSpace constructibility
cs = MyComponent.get_hyperparameter_search_space()
cs.get_default_configuration()

# 3. registration and ID visibility
add_classifier(MyClassifier)
assert "MyClassifier" in ClassifierChoice.get_components()
```

For feature/data preprocessors, also check that `fit(...).transform(...)` works
on a tiny in-memory array when the transformer is cheap. For estimators, avoid
long training; instantiate the wrapped estimator only on tiny arrays if needed.
