---
name: custom-components
description: "Extend auto-sklearn with custom classifiers, regressors, feature
  preprocessors, data preprocessors, ConfigSpace search spaces, registration,
  and component IDs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# custom-components

Use this sub-skill when a task needs to author, repair, register, or restrict
auto-sklearn components rather than merely run an existing estimator. The package
imports as `autosklearn`; the inspected package version was `0.16.0dev` /
`0.16.0.dev0`.

## Route here for

- Creating or fixing subclasses of:
  - `AutoSklearnClassificationAlgorithm`
  - `AutoSklearnRegressionAlgorithm`
  - `AutoSklearnPreprocessingAlgorithm`
- Implementing `get_properties()`, `get_hyperparameter_search_space()`,
  `fit()`, `predict()`, `predict_proba()`, and `transform()` for custom
  components.
- Calling `add_classifier()`, `add_regressor()`, or the feature/data
  `add_preprocessor()` registry functions.
- Choosing the correct custom component ID for `include` / `exclude` after
  registration.
- Replacing a broad built-in component search space with a custom wrapper that
  exposes fewer hyperparameters or narrower ranges.

## Route elsewhere

- Basic `AutoSklearnClassifier`, `AutoSklearnRegressor`, or `AutoSklearn2Classifier`
  usage: use [`../estimators/SKILL.md`](../estimators/SKILL.md).
- Ordinary built-in `include` / `exclude`, Dask, SMAC, budget, or ensemble
  configuration with no custom component code: use
  [`../search-and-parallelism/SKILL.md`](../search-and-parallelism/SKILL.md).
- Pandas dtypes, `feat_type`, target validation, custom metrics, resampling, or
  dataset compression: use
  [`../data-metrics-validation/SKILL.md`](../data-metrics-validation/SKILL.md).
- Long AutoML training runs for a new component: do not start them from this
  sub-skill. Validate the class, registry entry, and configuration space first.

## Operating procedure

1. Identify the component kind and registry:
   - classifier: base class `AutoSklearnClassificationAlgorithm`, registry
     `autosklearn.pipeline.components.classification.add_classifier`, include key
     `"classifier"`.
   - regressor: base class `AutoSklearnRegressionAlgorithm`, registry
     `autosklearn.pipeline.components.regression.add_regressor`, include key
     `"regressor"`.
   - feature preprocessor: base class `AutoSklearnPreprocessingAlgorithm`,
     registry `autosklearn.pipeline.components.feature_preprocessing.add_preprocessor`,
     include key `"feature_preprocessor"`.
   - data preprocessor: base class `AutoSklearnPreprocessingAlgorithm`, registry
     `autosklearn.pipeline.components.data_preprocessing.add_preprocessor`,
     include key `"data_preprocessor"`.
2. Read [`references/component-contracts.md`](references/component-contracts.md)
   before editing code. It contains the required properties, constants, built-in
   IDs, registry rules, and ConfigSpace rules.
3. If a safe starting file is useful, generate a no-training template:
   `python scripts/component_skeleton.py --kind classifier --class-name MyClassifier`
   or write it with `--output my_components.py`.
4. Keep the registration call in code that is imported before constructing the
   auto-sklearn estimator. For custom components, the ID used in `include` /
   `exclude` is the class name, for example `{"classifier": ["MyClassifier"]}`.
5. Validate without long training: import the module, call `get_properties()`,
   call `get_hyperparameter_search_space()`, register the class, and confirm the
   choice appears in the relevant component catalog or estimator configuration
   space.
6. For complete recipes, use [`references/workflows.md`](references/workflows.md).
   For errors, use [`references/troubleshooting.md`](references/troubleshooting.md).

## Quick validation snippets

Classifier registry check after importing the module that defines the class:

```python
from autosklearn.pipeline.components.classification import ClassifierChoice, add_classifier
from my_components import MyClassifier

add_classifier(MyClassifier)  # harmless if your module did not self-register
props = MyClassifier.get_properties()
required = {
    "shortname", "name", "handles_regression", "handles_classification",
    "handles_multiclass", "handles_multilabel", "handles_multioutput",
    "is_deterministic", "input", "output",
}
assert set(props) == required
cs = MyClassifier.get_hyperparameter_search_space()
assert "MyClassifier" in ClassifierChoice.get_components()
```

Estimator restriction check without starting a long run:

```python
import autosklearn.classification

automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=30,
    per_run_time_limit=10,
    include={"classifier": ["MyClassifier"]},
    initial_configurations_via_metalearning=0,
    smac_scenario_args={"runcount_limit": 1},
)
# Build or inspect the configuration space with tiny in-memory X/y before any
# expensive fit. If the ID is wrong, this should fail before training.
```

## Native evidence anchors for later verification

Relevant native candidates are the component registration unit checks, component
base-contract checks, and the extension examples. The extension examples are
fit-heavy and should remain skip-expensive unless a verifier deliberately bounds
them; prefer the bundled skeleton `--help` check and static registry/config-space
checks first.
