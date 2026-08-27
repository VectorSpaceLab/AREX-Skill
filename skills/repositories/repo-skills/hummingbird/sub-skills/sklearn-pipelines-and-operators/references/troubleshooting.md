# Sklearn pipeline and operator troubleshooting

Use this reference after basic conversion syntax is already correct. For missing backend packages, TorchScript/ONNX/TVM tracing requirements, CUDA, or performance tuning, route to the sibling backend sub-skill.

## Fast triage

1. Is every sklearn class in the fitted object covered by [operator coverage](operator-coverage.md)?
2. Is the source object fitted, and for search wrappers does it have `best_estimator_`?
3. Does the conversion input preserve the same column order, names, dtypes, and number of logical inputs as sklearn inference?
4. Are strings represented as supported string dtypes or pre-encoded categories?
5. For tree models, did you validate the same `tree_implementation` and `tree_op_precision_dtype` you plan to use?

## Symptom matrix

| Symptom or error | Likely cause | Corrective action |
| --- | --- | --- |
| `MissingConverter: Unable to find converter for model type ...` | The estimator class is not in the sklearn support list, or an optional source model is being handled as ordinary sklearn. | Check the coverage table. Replace or remove the unsupported child step. If the source is LightGBM, XGBoost, SparkML, Prophet, or ONNX-ML, route to the optional-source sub-skill. |
| `MissingConverter` mentioning tree implementation | `extra_config[constants.TREE_IMPLEMENTATION]` has an invalid value. | Use only `"gemm"`, `"tree_trav"`, or `"perf_tree_trav"`. Prefer constants over raw strings. |
| Assertion failure for `tree_op_precision_dtype` | Precision value is not `"float32"` or `"float64"`. | Use `extra_config={constants.TREE_OP_PRECISION_DTYPE: "float64"}` only when needed; otherwise omit it for the default `"float32"`. |
| Tree parity drifts after changing strategy | A different tree layout or float32 threshold/leaf precision changed numerical behavior. | Re-run parity for the final method (`predict`, `predict_proba`, `decision_function`, or `score_samples`). Try `TREE_OP_PRECISION_DTYPE="float64"`. If comparing strategies, use a backend that honors the tree implementation override. |
| A requested tree strategy appears ignored for ONNX-ML source conversion | When the source object is an ONNX-ML model, Hummingbird forces `tree_trav` internally to avoid a known GEMM issue. | Compare `gemm`/`perf_tree_trav`/`tree_trav` with a sklearn-source PyTorch conversion first. Route ONNX-specific output or ONNX-ML source details elsewhere. |
| `RuntimeError: Unable to find column name '...'` | A `ColumnTransformer` string selector cannot resolve that name from the logical inputs. | Pass a pandas DataFrame as `test_input`, or pass tuple inputs with `constants.INPUT_NAMES` matching selectors. Keep the same names at inference. |
| `NotImplementedError` about merging multiple columns from multiple variables | A `ColumnTransformer` branch selected columns that live in different logical inputs. | Use one wide 2-D input for columns that must be merged, split the branch into per-input selectors, or provide a DataFrame layout whose columns resolve consistently. |
| Unsupported dtype during input declaration | The representative input includes an unsupported dtype, often pandas object strings. | Use numeric NumPy arrays for numeric features. For string tracing, prefer NumPy `S`/`U` dtype arrays or pre-encoded integer categories. |
| Mixed numeric/string `ColumnTransformer` fails | The numeric branch is merged while the string branch needs separate string-compatible slices; pandas object dtype or missing names can break resolution. | Use a representative DataFrame/tuple with stable `input_names`; set `constants.MAX_STRING_LENGTH` if strings are present; consider pre-encoding string categories to integers before Hummingbird if object dtype remains unsupported. |
| `LabelEncoder` string transform raises an assertion on new data | Inference contains labels not present during fitting. | Include all expected labels during fitting, map unknowns before conversion, or use an encoding strategy with explicit unknown handling outside the converted model. |
| String encoder fails under TorchScript/ONNX-style tracing | The string input was not represented with a supported fixed-width string dtype or max length. | Provide representative string `test_input`, avoid object dtype, and set `constants.MAX_STRING_LENGTH` high enough for expected tokens. |
| `KNeighborsClassifier` / `KNeighborsRegressor` asks for `batch_size` | KNN converters require an explicit batch-size extra config. | Pass `extra_config={constants.BATCH_SIZE: X_eval.shape[0]}` or the intended inference partition size. Route throughput tuning to advanced backends/performance. |
| KNN metric or weight raises `NotImplementedError` | The metric or weight mode is outside the converter's supported set. | Use metric `minkowski`, `euclidean`, `manhattan`, `chebyshev`, `wminkowski`, `seuclidean`, or `mahalanobis`; use weights `uniform` or `distance`. |
| SVC `precomputed` kernel fails | The SVC converter supports only `linear`, `poly`, `rbf`, and `sigmoid`. | Refit with a supported kernel or keep the SVC outside the Hummingbird-converted segment. |
| User expects SVC probabilities | The SVC implementation explicitly has no class-probability output. | Validate `predict`; if probabilities are required, use a supported probabilistic classifier such as logistic regression, tree classifiers, naive Bayes, KNN classifier, or a different pipeline design. |
| Linear classifier rejects labels | Hummingbird's linear classifier conversion supports integer class labels. | Encode class labels to integers before fitting/conversion, and map predictions back after inference if needed. |
| Stacking conversion raises `ValueError` about ensemble method | The sklearn stacking method is not `predict_proba` or `predict` (for example, `decision_function`). | Choose base estimators/stacking configuration whose `stack_method_` resolves to `predict_proba` or `predict`, or keep stacking outside the converted model. |
| A `FunctionTransformer` does not preserve custom logic | Hummingbird only treats it as identity/concat at parser level. | Move arbitrary Python preprocessing before conversion, replace it with supported tensor-friendly sklearn transformers, or keep it outside the Hummingbird container. |
| Backend requires `test_input` | The selected backend is a tracing/compiled/export backend, not an operator-coverage issue. | Route to core conversion or advanced backends. Provide a representative sample with correct shape, dtype, names, and logical input count. |

## Tree strategy validation pattern

When a task asks to choose a tree strategy, do not stop at selecting a string value. Validate the strategy with the final output method and input layout.

```python
import numpy as np
from hummingbird.ml import constants, convert

strategies = ["gemm", "perf_tree_trav", "tree_trav"]
for strategy in strategies:
    hb = convert(
        fitted_tree_model,
        "torch",
        test_input=X_sample,
        extra_config={
            constants.TREE_IMPLEMENTATION: strategy,
            constants.TREE_OP_PRECISION_DTYPE: "float64",
        },
    )
    np.testing.assert_allclose(
        hb.predict(X_eval),
        fitted_tree_model.predict(X_eval),
        rtol=1e-6,
        atol=1e-6,
    )
```

Use `predict_proba`, `decision_function`, or `score_samples` instead when those are the downstream outputs. If an internal assertion is needed during debugging, inspect the converted PyTorch model's first operator type only after parity passes; internal class names are implementation details and should not replace behavior checks.

## Mixed numeric/string ColumnTransformer pattern

A hard but common case is a pipeline like:

- numeric columns -> `SimpleImputer` / `StandardScaler`;
- categorical string columns -> `OneHotEncoder(handle_unknown="ignore")`;
- final classifier -> `LogisticRegression` or a tree classifier.

Recommended approach:

1. Fit and test the sklearn pipeline first.
2. Use a small representative `test_input` that preserves names: a DataFrame with the same columns/order or a tuple of one-column arrays with `constants.INPUT_NAMES`.
3. Ensure string columns have supported string dtypes, not ambiguous object arrays, or pre-encode them to integer categories.
4. Set `constants.MAX_STRING_LENGTH` if longer inference strings are possible.
5. Convert to the simplest backend first, usually `"torch"`, and validate `predict` or `predict_proba` parity before moving to tracing/export/performance backends.

If this still fails, narrow the pipeline: convert the numeric-only branch and the categorical-only branch separately to identify whether the issue is operator support, input names, dtype, or the final estimator.
