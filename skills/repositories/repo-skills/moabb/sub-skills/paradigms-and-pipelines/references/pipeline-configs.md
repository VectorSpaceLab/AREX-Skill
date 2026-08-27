# Pipeline configuration

MOABB's configuration helper separates pipeline construction from benchmark
metadata. The runtime helper is:

```python
from moabb.pipelines.utils import create_pipeline_from_config

components = [
    {"name": "LogVariance", "from": "moabb.pipelines.features"},
    {
        "name": "LinearDiscriminantAnalysis",
        "from": "sklearn.discriminant_analysis",
        "parameters": {"solver": "svd"},
    },
]
pipeline = create_pipeline_from_config(components)
```

`create_pipeline_from_config(config)` expects a list. Each component mapping
must contain:

- `name`: attribute to retrieve from the imported module;
- `from`: importable module path;
- `parameters`: optional keyword mapping passed to the constructor.

It returns a sklearn `Pipeline` built with `make_pipeline`; generated step
names are lower-cased class names, so parameter-grid keys use names such as
`logvariance__...` or `lineardiscriminantanalysis__...` as appropriate. Inspect
`pipeline.get_params().keys()` before writing a grid.

## Full trusted-file schema

The directory parser understands a trusted YAML document with this shape:

```yaml
name: Log Variance LDA
paradigms:
  - LeftRightImagery
pipeline:
  - name: LogVariance
    from: moabb.pipelines.features
  - name: LinearDiscriminantAnalysis
    from: sklearn.discriminant_analysis
    parameters:
      solver: svd
param_grid:
  lineardiscriminantanalysis__solver:
    - svd
```

`name` is the benchmark label. `paradigms` is a list of compatible paradigm
class names. `pipeline` is the component list. `param_grid` is optional and is
kept as metadata by `parse_pipelines_from_directory`; it is not automatically
applied by `create_pipeline_from_config`. `citations` may be recorded as
metadata but does not affect construction.

Use a safe loader for a user-supplied file, validate that the root is a mapping,
that `pipeline` is a list, and that each component has string `name` and `from`.
Only then pass the component list to the dynamic importer. Do not use a config
from an untrusted source: arbitrary import paths and constructor arguments are
executable behavior. The package's directory parser is intended for trusted
local benchmark configurations; large benchmark folders and source checkout
configuration corpora are reference-only, not runtime dependencies of this
skill.

## Reusable recipes

### Imagery baseline

```yaml
name: Log Variance LDA
paradigms: [LeftRightImagery]
pipeline:
  - name: LogVariance
    from: moabb.pipelines.features
  - name: LinearDiscriminantAnalysis
    from: sklearn.discriminant_analysis
    parameters: {solver: svd}
```

### Covariance/tangent-space classifier

```yaml
name: Tangent Space Logistic Regression
paradigms: [LeftRightImagery, MotorImagery]
pipeline:
  - name: Covariances
    from: pyriemann.estimation
    parameters: {estimator: oas}
  - name: TangentSpace
    from: pyriemann.tangentspace
    parameters: {metric: riemann}
  - name: LogisticRegression
    from: sklearn.linear_model
    parameters: {C: 1.0, max_iter: 1000}
```

### SSVEP CCA

```yaml
name: SSVEP CCA
paradigms: [SSVEP]
pipeline:
  - name: SSVEP_CCA
    from: moabb.pipelines.classification
    parameters: {n_harmonics: 3}
```

For `SSVEP_TRCA`, use `n_fbands`, `is_ensemble`, `method`, and `estimator`.
For `SSVEP_TDCA`, use `n_fbands`, `n_components`, `n_delay`, and
`is_ensemble`. These parameters describe a learned classifier and must be
fitted only within an evaluation split.

## Config validation checklist

Before construction:

1. Confirm every module/class import with a small import check.
2. Confirm optional packages (`pyriemann`, PyYAML, and any MNE extras) are
   installed for the chosen recipe; do not silently replace a missing package
   with a different estimator.
3. Confirm the pipeline's expected array rank against the chosen paradigm.
4. Confirm `paradigms` matches the actual object; metadata does not enforce
   compatibility.
5. Confirm parameter names using `get_params(deep=True)`.
6. Keep YAML in the experiment/project configuration, not in this managed skill
   tree. The snippets above are bundled replacements for the useful config
   patterns; no original checkout file is required at runtime.
