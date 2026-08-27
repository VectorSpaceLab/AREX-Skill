# Custom component workflows

These recipes are designed for future agents who need concrete actions without
reopening the source repository. They avoid long AutoML training by validating
contracts, registries, and configuration spaces first.

## Workflow 1: generate a skeleton

Use the bundled script when you need a safe starting point:

```bash
python scripts/component_skeleton.py --kind classifier --class-name MyClassifier
python scripts/component_skeleton.py --kind regressor --class-name MyRegressor --output my_component.py
python scripts/component_skeleton.py --kind preprocessor --class-name MyPreprocessor
```

The script prints or writes a minimal component module with:

- correct base class import;
- required property keys including `handles_multioutput`;
- `ConfigurationSpace()` placeholder;
- methods that raise `NotImplementedError` until the wrapped estimator or
  transformer is added;
- registration comments showing which `add_*` function to call.

After generation, replace the placeholder `fit`, `predict`, `predict_proba`, or
`transform` bodies with a small scikit-learn wrapper.

## Workflow 2: author a custom classifier

1. Subclass `AutoSklearnClassificationAlgorithm` directly.
2. In `__init__`, store every ConfigSpace hyperparameter as an attribute and set
   `self.estimator = None`.
3. In `fit(X, y)`, coerce ConfigSpace values to Python types, create the wrapped
   classifier, call its `fit`, and return `self`.
4. In `predict(X)` and `predict_proba(X)`, raise `NotImplementedError()` if
   `self.estimator is None`, otherwise delegate to the wrapped estimator.
5. Return properties with classification enabled and regression disabled.
6. Return a valid `ConfigurationSpace`.
7. Register and include by class name.

Template pattern:

```python
from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import UniformFloatHyperparameter
import autosklearn.classification
import autosklearn.pipeline.components.classification
from autosklearn.pipeline.components.base import AutoSklearnClassificationAlgorithm
from autosklearn.pipeline.constants import DENSE, SPARSE, UNSIGNED_DATA, SIGNED_DATA, PREDICTIONS

class MyClassifier(AutoSklearnClassificationAlgorithm):
    def __init__(self, C=1.0, random_state=None):
        self.C = C
        self.random_state = random_state
        self.estimator = None

    def fit(self, X, y):
        from sklearn.linear_model import LogisticRegression
        self.C = float(self.C)
        self.estimator = LogisticRegression(C=self.C, random_state=self.random_state, max_iter=1000)
        self.estimator.fit(X, y)
        return self

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError()
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError()
        return self.estimator.predict_proba(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {
            "shortname": "MyClf",
            "name": "My Classifier",
            "handles_regression": False,
            "handles_classification": True,
            "handles_multiclass": True,
            "handles_multilabel": False,
            "handles_multioutput": False,
            "is_deterministic": True,
            "input": (DENSE, SPARSE, UNSIGNED_DATA, SIGNED_DATA),
            "output": (PREDICTIONS,),
        }

    @staticmethod
    def get_hyperparameter_search_space(feat_type=None, dataset_properties=None):
        cs = ConfigurationSpace()
        cs.add_hyperparameter(UniformFloatHyperparameter("C", lower=1e-4, upper=10.0, log=True, default_value=1.0))
        return cs

autosklearn.pipeline.components.classification.add_classifier(MyClassifier)

automl = autosklearn.classification.AutoSklearnClassifier(
    include={"classifier": ["MyClassifier"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
```

If the wrapped classifier lacks `predict_proba`, either choose a different
estimator or implement a calibrated probability interface. A classifier component
must expose `predict_proba` because classifier choice delegates that method.

## Workflow 3: author a custom regressor

1. Subclass `AutoSklearnRegressionAlgorithm` directly.
2. Implement `fit(X, y)` and `predict(X)`.
3. Set `handles_regression=True`, `handles_classification=False`, and
   `output=(PREDICTIONS,)`.
4. Decide `handles_multioutput` based on the wrapped regressor's target support.
5. Register with `autosklearn.pipeline.components.regression.add_regressor()`.
6. Include by class name under the `"regressor"` key.

Conditional ConfigSpace example:

```python
from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import CategoricalHyperparameter, UniformFloatHyperparameter
from ConfigSpace.conditions import EqualsCondition

cs = ConfigurationSpace()
kernel = CategoricalHyperparameter("kernel", ["rbf", "polynomial"], default_value="rbf")
gamma = UniformFloatHyperparameter("gamma", 1e-5, 1.0, log=True, default_value=0.1)
degree = UniformFloatHyperparameter("degree", 2, 5, default_value=3)
cs.add_hyperparameters([kernel, gamma, degree])
cs.add_condition(EqualsCondition(degree, kernel, "polynomial"))
```

Check that every default belongs to its range. Invalid defaults or conditions
surface before fitting when `get_default_configuration()` is called.

## Workflow 4: author a feature preprocessor

Feature preprocessors run between data preprocessing and the estimator.

1. Subclass `AutoSklearnPreprocessingAlgorithm` directly.
2. Implement `fit(X, y=None)` and `transform(X)`.
3. Use `self.preprocessor` for a wrapped scikit-learn transformer.
4. In properties, set task handles (`handles_classification`,
   `handles_regression`, multiclass/multilabel/multioutput) to match the
   transformer's behavior.
5. Set `input` to the data layout/signs the transformer accepts.
6. Set `output` to the transformed layout/signs or `(INPUT,)` if unchanged.
7. Register with
   `autosklearn.pipeline.components.feature_preprocessing.add_preprocessor()`.
8. Include by class name under `"feature_preprocessor"`.

Example include:

```python
autosklearn.pipeline.components.feature_preprocessing.add_preprocessor(MyPreprocessor)
automl = autosklearn.classification.AutoSklearnClassifier(
    include={"feature_preprocessor": ["MyPreprocessor"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
```

For a pass-through feature step, consider the built-in ID `no_preprocessing` for
ordinary use. Only add a custom pass-through if you need custom registry behavior
or custom properties.

## Workflow 5: author a data preprocessor

Data preprocessors are earlier pipeline components and can alter how raw feature
types are handled. They use the same `AutoSklearnPreprocessingAlgorithm` base
class but register in a different module:

```python
import autosklearn.pipeline.components.data_preprocessing

autosklearn.pipeline.components.data_preprocessing.add_preprocessor(MyDataPreprocessor)

automl = autosklearn.classification.AutoSklearnClassifier(
    include={"data_preprocessor": ["MyDataPreprocessor"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
```

A safe no-op data preprocessor has `fit` returning `self`, `transform` returning
`X`, `input` covering the accepted layouts, and `output=(INPUT,)`. Use caution:
turning off built-in data preprocessing can remove imputation, categorical
encoding, text handling, and scaling. If the task is really about dtype or
`feat_type` correctness, route to the data-metrics-validation sub-skill.

## Workflow 6: fix missing property keys and wrong include ID

Symptom pattern: registration raises `ValueError: Property handles_multioutput
not specified...`, or estimator construction raises `Trying to include unknown
component: my_classifier`.

Repair steps:

1. Compare `set(MyComponent.get_properties())` to the exact required key set in
   `component-contracts.md`.
2. Add missing `handles_multioutput`; set it from actual target support.
3. Remove extra keys that registration rejects.
4. Ensure `input` and `output` are tuples/lists of constants, not strings.
5. Confirm direct base class: `AutoSklearnClassificationAlgorithm in MyComponent.__bases__`.
6. Register the class before constructing the estimator.
7. Use the class name in `include`, not `shortname`, `name`, module name, or a
   lower-case built-in-style ID:

```python
add_classifier(MyClassifier)
include={"classifier": ["MyClassifier"]}
```

Then perform no-training checks:

```python
from autosklearn.pipeline.components.classification import ClassifierChoice
assert "MyClassifier" in ClassifierChoice.get_components()
cs = MyClassifier.get_hyperparameter_search_space()
cs.get_default_configuration()
```

## Workflow 7: restrict or narrow a component search space

Choose the least invasive pattern:

- To use only a built-in component: route to search-and-parallelism and set
  `include={"classifier": ["random_forest"]}` or the appropriate key.
- To remove one built-in while keeping others: use `exclude` with the built-in
  ID, for example `exclude={"classifier": ["random_forest"]}`.
- To tune fewer hyperparameters or narrower ranges than a built-in exposes:
  create a custom wrapper class and register it.

Custom-only strict search:

```python
add_classifier(CustomRandomForest)
automl = autosklearn.classification.AutoSklearnClassifier(
    include={"classifier": ["CustomRandomForest"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
```

Replacement-plus-others search:

```python
add_classifier(CustomRandomForest)
automl = autosklearn.classification.AutoSklearnClassifier(
    exclude={"classifier": ["random_forest"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
```

After constructing the estimator, inspect or build the configuration space on a
tiny in-memory dataset before calling `fit`. Confirm the old built-in ID is not
present and the custom class name is present.

## Workflow 8: validate sparse/dense and signed/unsigned compatibility

auto-sklearn uses component `input` and `output` properties to build legal
pipelines and forbidden combinations. For sparse data:

- If `dataset_properties["sparse"]` is true, components whose `input` lacks
  `SPARSE` are filtered out.
- A preprocessor with `output=(DENSE, ...)` can make downstream components see
  dense data.
- A preprocessor with `output=(SPARSE, ...)` can make downstream components see
  sparse data.
- A component that outputs `INPUT` preserves the current sparse/dense state.

For signed data:

- If data is unsigned and a component requires signed values only, pipeline
  matching can reject the combination.
- If a transformer can create negative values, include `SIGNED_DATA` in output.
- If it preserves non-negativity, include `UNSIGNED_DATA` or `INPUT` as
  appropriate.

Do not overstate compatibility just to pass search-space construction; that
moves the failure into a later fit.

## Workflow 9: final bounded validation sequence

Before a long component training run, use this sequence:

1. `python scripts/component_skeleton.py --help` if the skeleton helper changed.
2. Import the custom module; ensure registration has no exception.
3. Validate exact property keys and no unknown keys.
4. Validate `ConfigurationSpace` construction and default configuration.
5. Confirm registry visibility through `ClassifierChoice`, `RegressorChoice`,
   `FeaturePreprocessorChoice`, or `DataPreprocessorChoice`.
6. Create an estimator with `include` targeting the custom class name and very
   small budgets (`initial_configurations_via_metalearning=0`,
   `smac_scenario_args={"runcount_limit": 1}`) only if the user approves even a
   bounded fit.
7. If prediction or transform is called before fit, expect the component to raise
   `NotImplementedError()` rather than silently using an uninitialized wrapped
   estimator.
