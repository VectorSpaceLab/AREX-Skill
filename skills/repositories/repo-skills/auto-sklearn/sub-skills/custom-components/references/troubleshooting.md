# Custom component troubleshooting

Use this matrix to diagnose custom classifiers, regressors, feature
preprocessors, and data preprocessors. Prefer these no-training checks before
starting any AutoML run.

## Fast diagnostic checklist

```python
required = {
    "shortname", "name", "handles_regression", "handles_classification",
    "handles_multiclass", "handles_multilabel", "handles_multioutput",
    "is_deterministic", "input", "output",
}
props = MyComponent.get_properties()
assert set(props) == required, (set(props) - required, required - set(props))
cs = MyComponent.get_hyperparameter_search_space()
cs.get_default_configuration()
```

Then register the class and confirm its ID:

```python
add_classifier(MyClassifier)
assert "MyClassifier" in ClassifierChoice.get_components()
```

For regressors use `RegressorChoice`; for feature preprocessors use
`FeaturePreprocessorChoice`; for data preprocessors use `DataPreprocessorChoice`.

## Error and symptom matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `ValueError: Property handles_multioutput not specified for algorithm ...` | `get_properties()` omitted a required key. This version validates `handles_multioutput` even though older prose may not emphasize it. | Add `"handles_multioutput": True/False` based on actual support. Recheck exact key set. |
| `ValueError: Property ... must not be specified...` | `get_properties()` has an extra key. | Remove every key outside the exact required set. Keep additional notes in comments, not properties. |
| `TypeError: add_component works only with a subclass of ...` | Passed an instance, plain scikit-learn estimator, wrong base class, or indirect subclass. Registration requires a class whose immediate base is the expected auto-sklearn base. | Pass the class object, not `MyClass()`. Subclass `AutoSklearnClassificationAlgorithm`, `AutoSklearnRegressionAlgorithm`, or `AutoSklearnPreprocessingAlgorithm` directly. Use the matching registry. |
| `Trying to include unknown component: ...` | The class was not registered before estimator construction, or the `include` ID is wrong. | Import the module that runs `add_*` first. Use the class name (`"MyClassifier"`), not `shortname`, `name`, filename, or lower-case guessed ID. |
| Custom component registered but does not appear in configuration space | Dataset properties or component properties filter it out; include/exclude conflict; sparse/multilabel/multioutput flags incompatible. | Check `handles_*`, `input`, and `output`. For sparse data, include `SPARSE` only if supported. For multilabel/multioutput, set flags truthfully. |
| `ValueError: include and exclude cannot be used together` | Both include and exclude were passed to the same choice. | Use only one. For strict custom search, use `include`; for replacing one built-in while keeping others, use `exclude` for the built-in ID and register your class. |
| `No classifiers found`, `No regressors found`, or `No preprocessors found` | Restrictions or properties filtered every component. | Relax include/exclude, add a compatible no-op preprocessor where appropriate, or correct `handles_*` / sparse/dense properties. |
| `No valid pipeline found` or `Cannot find a legal default configuration` | The chosen estimator and preprocessor properties produce forbidden pipeline combinations. | Inspect `input`/`output` constants. Ensure feature preprocessor output is compatible with downstream classifier/regressor input. Relax search restrictions. |
| ConfigSpace raises about invalid default value | A hyperparameter default is outside its range or not in categorical choices. | Set defaults inside bounds and choices. Call `cs.get_default_configuration()` during validation. |
| ConfigSpace condition errors | Condition references a hyperparameter before it is added or uses an invalid parent value. | Add all hyperparameters before conditions. Ensure condition values exist in parent choices. |
| `Cannot set hyperparameter ... because the hyperparameter does not exist` | ConfigSpace hyperparameter name is not an attribute initialized in `__init__`. | Add `self.<name> = <default>` in `__init__` for every hyperparameter name. |
| Wrapped estimator gets string values for numeric params | ConfigSpace values were not converted before constructing wrapped estimator. | Convert in `fit()`: `int(...)`, `float(...)`, sentinel-to-`None`, tuple/list conversion as needed. |
| `NotImplementedError` from `predict`, `predict_proba`, or `transform` before fit | The method correctly guards against uninitialized wrapped object, or `fit` never set `self.estimator` / `self.preprocessor`. | If before fit, call `fit` first. If after fit, set the wrapped object in `fit` and return `self`. |
| Classifier fails because `predict_proba` is missing | Wrapped estimator lacks probability predictions. | Pick a probability-capable estimator, calibrate probabilities, or do not use it as an auto-sklearn classifier component. |
| Sparse data fails inside wrapped estimator | Properties claimed `SPARSE` but wrapped estimator/transformer only accepts dense data. | Remove `SPARSE` from `input` or add a densifying transformer and advertise `output` accurately. |
| Dense data unexpectedly converted to sparse or sparse to dense | Preprocessor `output` declared `SPARSE` or `DENSE`, causing pipeline state transition. | If the transformer preserves layout, use `(INPUT,)`. Otherwise ensure downstream component properties accept the new layout. |
| Multilabel or multioutput task filters out component | `handles_multilabel` or `handles_multioutput` is false. | Set true only if the wrapped model has been tested for that target shape. Otherwise choose a compatible estimator or route to a different component. |
| Data preprocessor disables expected dtype handling | Custom data preprocessor replaced the built-in feature-type pipeline. | If the issue is pandas/string/categorical dtype handling, route to data-metrics-validation. If intentionally custom, implement encoding/imputation responsibilities explicitly. |

## Property debugging details

Registration validates properties using `set(classifier.get_properties())`, so
values are not checked deeply at registration time. Pipeline construction later
uses `input`, `output`, and `handles_*` to filter components. Catch mistakes early:

```python
from autosklearn.pipeline.constants import DENSE, SPARSE, SIGNED_DATA, UNSIGNED_DATA, PREDICTIONS, INPUT

props = MyComponent.get_properties()
assert isinstance(props["input"], (tuple, list))
assert isinstance(props["output"], (tuple, list))
allowed_input = {DENSE, SPARSE, SIGNED_DATA, UNSIGNED_DATA}
allowed_output = {DENSE, SPARSE, SIGNED_DATA, UNSIGNED_DATA, PREDICTIONS, INPUT}
assert set(props["input"]).issubset(allowed_input)
assert set(props["output"]).issubset(allowed_output)
```

Classifiers and regressors should output `(PREDICTIONS,)`. A feature preprocessor
that returns the same representation can output `(INPUT,)`; one that densifies
must output `DENSE` and the correct sign constants.

## Registration state debugging

The `add_*` functions add to in-process registries. Registration is not a
package install step and is not persistent across Python processes unless the
module containing the registration call is imported each time.

Good pattern:

```python
# my_components.py
class MyClassifier(AutoSklearnClassificationAlgorithm):
    ...

autosklearn.pipeline.components.classification.add_classifier(MyClassifier)
```

Then, in the script or notebook that constructs the estimator:

```python
import my_components  # runs registration side effect
import autosklearn.classification

automl = autosklearn.classification.AutoSklearnClassifier(
    include={"classifier": ["MyClassifier"]},
)
```

If duplicate registration occurs in the same process, the registry entry is
replaced under the same class-name key. If you need deterministic cleanup in a
unit test, remove the class-name key from the relevant `additional_components`
registry after the test.

## ConfigSpace debugging details

When narrowing hyperparameters, most errors surface without fitting:

```python
cs = MyComponent.get_hyperparameter_search_space()
print(cs)
cs.get_default_configuration()
for hp in cs.get_hyperparameters():
    print(hp.name, hp.default_value)
```

Common fixes:

- For log-scaled floats/integers, lower bounds must be positive.
- Categorical defaults must be one of the listed choices and have the same type.
- Conditions should be added after hyperparameters.
- A condition's parent value must exist in the parent hyperparameter choices.
- If a hyperparameter is conditional, the wrapped estimator should tolerate it
  being absent/inactive or the component should fill a safe default in `fit()`.

## Include/exclude ID debugging

Built-in IDs are lower-case catalog names such as `random_forest` or
`no_preprocessing`. Custom third-party IDs are class names such as
`CustomRandomForest`. Do not mix the two naming schemes.

Examples:

```python
# Built-in random forest only
include={"classifier": ["random_forest"]}

# Custom class only after add_classifier(CustomRandomForest)
include={"classifier": ["CustomRandomForest"]}

# Keep all compatible classifiers except built-in random_forest; custom class remains available
exclude={"classifier": ["random_forest"]}
```

If the task is only to choose built-in IDs, route to search-and-parallelism for
resource and search guidance.

## Sparse/dense mismatch debugging

Pipeline compatibility is based on declared properties:

- `SPARSE` absent from `input` means the component is unavailable for sparse
  data until an upstream densifier changes the representation.
- `DENSE` absent from `input` means the component is unavailable for dense data.
- `INPUT` in preprocessor output preserves the representation.
- `DENSE` or `SPARSE` in output changes representation for downstream steps.

If a task fails only when input is sparse, do not route immediately to data dtype
handling. First inspect the custom component's properties. Route to
data-metrics-validation only when the issue is accepted data format, pandas
column dtype, `feat_type`, string/categorical behavior, or target validation.

## Native verification candidates

For later integrated verification, the most relevant native anchors are:

- component registration checks similar to `test_add_classifier` and
  `test_add_preprocessor`;
- component base tests that verify fit/predict/predict_proba/transform behavior
  on tiny data;
- built-in component catalog inspection;
- extension examples treated as skip-expensive unless tightly bounded.

Do not run long component training during ordinary troubleshooting. Validate the
contract and registry first, then ask before any bounded `fit`.
