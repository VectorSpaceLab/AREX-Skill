# Cross-cutting troubleshooting

Read this reference when the export problem is not specific to one target language.

## Installation and import

`m2cgen` requires Python >=3.7 and NumPy. Install the package in the same environment that will run the exporter. A successful import only proves the base package is available; an estimator's originating library is still required to fit or unpickle that model.

Use `python -m m2cgen` if the `m2cgen` console script is not on `PATH`. If both fail, verify the active interpreter with `python -c "import sys; print(sys.executable)"` and reinstall into that interpreter.

## Optional estimator libraries

A serialized scikit-learn, statsmodels, lightning, XGBoost, or LightGBM model carries a reference to its defining class. Install the matching library and preferably a compatible version before calling the CLI. Do not treat a missing optional library as an m2cgen language-support failure.

## Model and API validation

- Export only fitted model objects. A missing `coef_`, `tree_`, booster dump, or fitted result state usually means the estimator was not fitted.
- Support is keyed to runtime module prefix and class name. A custom wrapper or subclass can produce `NotImplementedError` even if its parent class is listed as supported.
- For meta-estimators, validate the inner estimator too; RANSAC requires a supported fitted base estimator.
- Use the public `export_to_*` signature for the selected language. API kwargs are not a generic options dictionary.

## Serialization and CLI

Pickle/joblib loading occurs before model assembly. If unpickling raises `ImportError`, install the package defining the model and make custom classes importable from a top-level module. Use `--pickle-lib joblib` only for a joblib-written file. When stdin fails, retry with a file path first to distinguish shell-pipe problems from deserialization problems.

## Numerical validation

Generated code uses double/float64-style arithmetic, but target runtimes and original model libraries may cast inputs differently. Compare against the correct original output (`decision_function` for linear/SVM classifiers, probability output for tree/forest/boosting classifiers) with a tolerance rather than exact string or exact floating-point equality.

## Size and recursion

Deep trees and large ensembles can exceed Python recursion depth or produce source too large for a target compiler/interpreter. Reduce estimator count/depth first; then raise CLI `--recursion-limit` or `sys.setrecursionlimit` in an API caller. Visual Basic/VBA has especially restrictive expression, procedure, line, and stack limits.

## Model-family-specific failures

- SVM: check the kernel name; callable kernels are not supported.
- Statsmodels: check constant-position detection and the supported inverse-link map.
- XGBoost/LightGBM: check booster dump format and objective/booster support; changing the target language does not fix an unsupported model representation.
