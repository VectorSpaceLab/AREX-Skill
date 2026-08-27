# Pipeline and data formats

Use this reference when a Hummingbird task involves sklearn composition, DataFrame columns, tuple/multiple inputs, column names, or strings. For basic `convert(...)` syntax, use the core conversion sub-skill first.

## Accepted input layouts

| Layout | How Hummingbird treats it | Use when | Main pitfalls |
| --- | --- | --- | --- |
| Single 2-D NumPy array | One logical input named `"input"` by default. Column indices are positions in the array. | Ordinary tabular sklearn estimators and simple pipelines. | Column names are unavailable; string column selectors in `ColumnTransformer` cannot resolve. |
| Tuple of 2-D NumPy arrays | Multiple logical inputs. `n_inputs` equals tuple length and `n_features` is the sum of input widths. | Multiple-input ONNX/TorchScript-style schemas or one-input-per-column conversion. | A single `ColumnTransformer` selector cannot merge columns from different logical inputs unless the parser is in a multiple-input slicing path. Keep selectors aligned with one input or use a single wide array. |
| pandas DataFrame as `test_input` | Hummingbird splits each column into a one-column array, sets `n_inputs` to the column count, and derives `input_names` from DataFrame columns. | Column-name selectors, mixed named features, and ONNX schema naming. | Future DataFrames must keep the same columns/order. pandas object-string dtypes can be harder than NumPy `S`/`U` string arrays. |
| pandas DataFrame only at inference time | If conversion did not receive a `test_input`, the container may convert the DataFrame with `.values` rather than preserving per-column names. | Simple numeric arrays where names do not matter. | Name-based `ColumnTransformer` selectors or multi-input schemas can fail or silently use a different layout. |

For tracing backends, output schemas, and model I/O details, route backend-specific work to the appropriate sibling sub-skill after fixing the sklearn layout.

## `ColumnTransformer` behavior

Hummingbird parses fitted `ColumnTransformer.transformers_`. Supported selector forms include integers, strings, slices, and lists of selectors. The parser handles:

- `"drop"` by skipping that branch;
- `"passthrough"` by forwarding the selected input slice;
- `transformer_weights` by inserting a multiply before concatenation;
- multiple transformed branches by concatenating their outputs.

Column name resolution depends on the logical input names available during conversion. A string selector such as `"age"` resolves only if one logical input is named `"age"`. The most reliable ways to provide names are:

```python
from hummingbird.ml import convert, constants

# DataFrame path: names come from columns.
hb = convert(fitted_pipeline, "torch", test_input=X_sample_df)

# Tuple path: names come from explicit config.
hb = convert(
    fitted_pipeline,
    "onnx",
    test_input=tuple_inputs,
    extra_config={
        constants.INPUT_NAMES: ["age", "fare", "pclass"],
        constants.OUTPUT_NAMES: ["score"],
    },
)
```

If `constants.INPUT_NAMES` is set, its length must match the number of logical inputs. `constants.OUTPUT_NAMES` must match the number of Hummingbird graph outputs.

### Column merging rule

When a transformer branch receives more than one selected column, Hummingbird usually inserts a concat before parsing that branch because many downstream operators expect one input tensor. It avoids this merge when the branch itself is a `OneHotEncoder`, a nested `ColumnTransformer`, or a `FunctionTransformer` (or a pipeline whose first step is one of those).

This matters for mixed numeric/string pipelines:

- Numeric branches such as `StandardScaler` over several columns are usually merged into a dense tensor.
- A categorical branch beginning with `OneHotEncoder` keeps separate column slices, which is useful for integer or string categories.
- A branch that spans columns from different logical inputs can raise a merge-related `NotImplementedError`; use a single wide input, split selectors per input, or pass a DataFrame/tuple schema that matches the intended selection.

## `Pipeline` and `FeatureUnion`

`Pipeline` is parsed sequentially: each step's output becomes the next step's input. The final converted container exposes the final pipeline method family, such as `transform`, `predict`, or `predict_proba`.

`FeatureUnion` is parsed in parallel: each transformer sees the same inputs, optional `transformer_weights` are applied, and branch outputs are concatenated. Use it for parallel feature transforms only when every branch transformer is supported.

`FunctionTransformer` is limited to identity behavior for one input or concat behavior for multiple inputs. Do not expect arbitrary Python callables to be converted into tensor code.

## String features and encoders

Standalone sklearn `OneHotEncoder` and `LabelEncoder` have string-aware Hummingbird implementations. Internally, strings are encoded as fixed-width integer tensors, and word length is rounded to a multiple of four bytes because the conversion uses `int32` chunks.

Practical guidance:

- Use NumPy string dtypes (`S` or `U`) for tracing inputs when possible. Pure object arrays are a common source of unsupported dtype failures.
- Let Hummingbird infer `constants.MAX_STRING_LENGTH` from fitted encoders, or provide it explicitly when the inference-time vocabulary may include longer strings.
- Keep categories consistent with training. `LabelEncoder` rejects unseen labels; `OneHotEncoder(handle_unknown="ignore")` is safer for categorical feature branches that may see unknown categories.
- For mixed numeric/string `ColumnTransformer` pipelines, pass representative `test_input` with stable input names. If pandas object-string columns fail, either convert the relevant columns to NumPy string dtype before conversion or pre-encode categories to integers before the Hummingbird step.

Example string-aware config:

```python
from hummingbird.ml import constants, convert

hb = convert(
    fitted_pipeline,
    "torch",
    test_input=X_sample,
    extra_config={constants.MAX_STRING_LENGTH: 32},
)
```

## Multiple-input schemas

Use tuple inputs when the converted artifact needs separate model inputs. Each tuple element must be a 2-D NumPy array. For one-input-per-column schemas:

```python
import numpy as np
from hummingbird.ml import convert, constants

column_inputs = tuple(np.split(X_sample, X_sample.shape[1], axis=1))
extra_config = {
    constants.INPUT_NAMES: ["A", "B", "C", "D", "E"],
    constants.OUTPUT_NAMES: ["score"],
}
hb = convert(fitted_pipeline, "onnx", column_inputs, extra_config=extra_config)
```

Then inference must pass the same tuple structure, or a DataFrame that Hummingbird can split into equivalent one-column arrays when the container was created with a DataFrame-aware `test_input`.

## Layout parity checklist

Before considering a pipeline conversion usable, check:

1. The fitted sklearn pipeline can run on the exact representative input chosen for Hummingbird conversion.
2. Every nested estimator/transformer is covered by the operator coverage reference.
3. Column names or indices resolve the same way during conversion and inference.
4. String columns are not silently converted to unsupported object arrays.
5. The desired output method family is validated against sklearn on held-out or representative data.
6. Any tree strategy or precision override is included in the parity check, not only in final deployment code.
