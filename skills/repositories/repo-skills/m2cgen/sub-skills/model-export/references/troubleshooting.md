# Troubleshooting

## `NotImplementedError: Model '...' is not supported`

**Cause:** the runtime type of the fitted estimator is outside the supported assembler map.

**Fix:**

- Export the nearest supported estimator from the same family instead.
- For `RANSACRegressor`, make sure the fitted base estimator is supported.
- For XGBoost / LightGBM, use a supported booster or objective variant.
- Beware subclasses and wrappers: m2cgen support is keyed by runtime module prefix and class name, so a subclass can fail even when it inherits from a supported estimator.

## Unsupported language target

**CLI symptom:** argument parsing rejects the value passed to `--language`.

**API symptom:** code tries to call a non-existent helper such as `export_to_typescript`.

**Fix:** choose one of the supported targets in `cli-reference.md`. If the desired runtime is unavailable, export to a nearby language only when the generated syntax is actually compatible with your downstream build system.

## `RecursionError: maximum recursion depth exceeded`

**Cause:** very large or deeply nested ensembles can exceed Python recursion depth during AST assembly or interpretation.

**Fix:**

- Reduce tree count or depth when possible.
- Use a smaller trained ensemble for code generation if approximate behavior is acceptable.
- Increase CLI recursion depth, for example `--recursion-limit 10000`.
- With the Python API, raise recursion depth in the calling process before export.

## `ImportError` or unpickling failure during CLI export

**Cause:** the serialized model's defining package is missing, or the model class is not importable at module top level.

**Fix:**

- Install the package that defines the estimator class.
- Make sure custom estimator classes live in an importable top-level module, not only inside a notebook cell or local function.
- Use `--pickle-lib joblib` only if `joblib` is installed and the file was written by joblib.
- If stdin piping fails, first verify the same bytes work from a file path to separate shell-pipe issues from unpickling issues.

## Optional dependency missing

**Cause:** m2cgen has a small base dependency set, but it does not vendor model libraries. A fitted scikit-learn, statsmodels, lightning, XGBoost, or LightGBM object still needs its original library available when exporting or unpickling.

**Fix:** install the library that produced the fitted estimator. Pin close to the version used when the model was serialized when possible.

## Unsupported kernel, link, or objective

**SVM cause:** a custom callable kernel or unsupported kernel name is present.

**Statsmodels / GLM cause:** the link function class is not in the supported inverse-link map, or statsmodels cannot identify the constant position.

**Boosting cause:** the LightGBM objective or XGBoost booster dump format is outside supported variants.

**Fix:** retrain or convert to a supported kernel, link, booster, or objective. Do not assume changing the output language can solve model-assembly limitations.

## Generated code returns numeric values that differ from Python model output

**Cause:** generated code uses `float64` / `double` style semantics, while native library prediction code or the target language can cast inputs differently. Small floating-point differences are expected across languages.

**Fix:**

- Cast inputs to the numeric type expected by the generated function.
- Compare with a tolerance instead of exact equality.
- For tree and forest models, check whether the original library casts feature arrays before prediction.
- Confirm you are comparing against the correct output method: decision scores for linear/SVM classifiers, probabilities for tree/forest/boosting classifiers.

## Generated code is too large or target compiler rejects it

**Cause:** large models produce large generated expressions or helper methods.

**Fix:**

- Reduce model size, depth, or number of estimators.
- Prefer a language target with helper/subroutine support if suitable.
- For Visual Basic / VBA-compatible output, large generated code can hit host limits such as line length, expression depth, static data size, procedure size, stack depth, or too many names.

## Console script not found

**Cause:** the package is importable but the environment's script directory is not on `PATH`, or the package was installed without exposing console scripts.

**Fix:** use `python -m m2cgen` or repair the environment's `PATH` / installation.