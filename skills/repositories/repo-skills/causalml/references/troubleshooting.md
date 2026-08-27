# CausalML cross-cutting troubleshooting

Use this file for package-wide install/import and workflow-selection issues. For model-family-specific failures, continue to the nearest sub-skill troubleshooting reference.

## Core import fails

Run:

```bash
python scripts/check_env.py
```

If core imports fail:

1. Confirm the active Python environment has CausalML installed.
2. Confirm Python satisfies the package requirement for the installed version.
3. Reinstall the package from a clean wheel or rebuild editable source extensions after dependency changes.
4. Run `python -m pip check` to catch incompatible dependency versions.

If a harmless message like `Failed to import duecredit` appears while imports otherwise succeed, it means the optional citation helper is absent. It does not normally block CausalML workflows.

## XGBoost native library or OpenMP errors

Some meta-learners and propensity models use XGBoost. If XGBoost imports but its native library cannot load, CausalML converts that condition into a RuntimeError with OpenMP guidance. On macOS, install an OpenMP runtime such as:

```bash
brew install libomp
# or, in a Conda environment:
conda install -c conda-forge llvm-openmp
```

Then restart Python and retry the import. On Linux, check the XGBoost wheel, system compiler runtime, and container base image.

## Cython tree-extension import errors

Tree classes depend on compiled extensions. If imports fail with Cython, scikit-learn random-utility, `DEFAULT_SEED`, or binary ABI errors:

1. Remove stale build artifacts from the package checkout if using editable source.
2. Reinstall/rebuild CausalML against the currently active NumPy, SciPy, and scikit-learn versions.
3. Avoid mixing old compiled `.so`/`.pyd` files with newer dependency versions.
4. Confirm `from causalml.inference.tree import CausalTreeRegressor` succeeds before using tree sub-skill recipes.

Current source includes a local random utility to avoid the known scikit-learn `DEFAULT_SEED` signature mismatch, so a fresh build with supported dependencies should import cleanly.

## Graphviz or tree-plot rendering fails

`uplift_tree_plot(...)` returns a `pydotplus` graph object, but rendering methods such as `create_png()` need both Python `pydotplus` and the Graphviz system executable. If rendering fails:

- Install Graphviz with the operating-system package manager.
- Confirm `dot` is on `PATH`.
- Fall back to `uplift_tree_string(...)` for a text rendering when image output is not required.

Tree fitting and prediction do not require Graphviz.

## Optional deep backend import errors

Optional neural models are not part of the minimal core install:

| Import failure | Install |
| --- | --- |
| `causalml.inference.tf` | `pip install "causalml[tf]"` |
| `causalml.inference.torch` | `pip install "causalml[torch]"` |
| `causalml.inference.jax` | `pip install "causalml[jax]"` |

Use [../sub-skills/deep-models/references/backend-setup.md](../sub-skills/deep-models/references/backend-setup.md) after installing the selected backend. CUDA/GPU use depends on the backend's own accelerator build; small CausalML smoke checks can run on CPU.

## Argument-order warnings

Current CausalML wraps many estimators with an argument-order migration shim. Use keywords:

```python
learner.fit(X=X, treatment=treatment, y=y, p=p)
learner.fit_predict(X=X, treatment=treatment, y=y, p=p)
```

Do not write new code with ambiguous positional calls such as `fit(X, y, treatment)`. See [../sub-skills/causal-estimation/references/api-contracts.md](../sub-skills/causal-estimation/references/api-contracts.md) for model-family contracts.

## Stale or absent API names

Current CausalML 0.17.0 does not expose these names as public runtime APIs:

- `causalml.inference.nn`
- `BaseIVRegressor`
- `BaseDRIVClassifier`
- `make_uplift_regression` from `causalml.dataset`
- `FeatureEffectExplainer` from `causalml.features`
- `SensitivityRandomFeature`
- top-level `save_model` / `load_model` functions for classical learners

Use the sub-skill references for current alternatives.

## Data and treatment-label problems

Common cross-workflow data failures:

- Treatment labels do not include the declared `control_name`.
- Binary APIs receive strings instead of `0/1` treatment indicators.
- Propensity scores contain `0`, `1`, `NaN`, or infinite values.
- Feature matrices contain object columns that were not encoded before model fitting.
- Metric DataFrames include raw feature columns, causing metrics to treat features as model scores.
- Outcome, treatment, true-effect, or post-treatment columns leak into model features.

Route data preparation to [../sub-skills/data-preparation/](../sub-skills/data-preparation/) and scoring/decision failures to [../sub-skills/analysis-and-decision/](../sub-skills/analysis-and-decision/).

## Persistence and version mismatch warnings

Classical estimators use `learner.save(path)`, `ClassName.load(path)`, and `causalml.inference.serialization.load_learner(path)`. Loading a model saved with a different CausalML version can emit a version-mismatch warning; retrain when exact prediction reproducibility matters.

TensorFlow/JAX neural checkpoints use backend-specific save/load methods documented in [../sub-skills/deep-models/](../sub-skills/deep-models/). Torch/Pyro CEVAE has no CausalML wrapper-level `save`/`load` API.
