# API reference

## Shared rules

- Mapper-family objects work on a copied input, not the original object.
- `memoize=True` caches outputs by a hash key; the default key is `get_hashable`.
- `reset_cache()` clears the memoization cache.
- `Mapper.run` and `Preprocessor.run` must use fixed arguments only; `*args` / `**kwargs` are rejected.
- `None` is a valid transform result and means “drop this transformed copy”.

### Hashability helper

`get_hashable(obj)` turns common transform inputs into cacheable keys:

- hashable objects are returned unchanged
- `SimpleNamespace` is converted through its attributes
- `dict` and `pandas.Series` become nested `frozenset` values
- `list` and `tuple` become nested tuples
- `numpy.ndarray` becomes its byte payload
- anything else raises `ValueError`

Use a custom `memoize_key` when the default key cannot represent your input or when only one stable field should drive caching.

## Mapper family

| Symbol | Signature | Return | Notes |
| --- | --- | --- | --- |
| `BaseMapper` | `BaseMapper(name, pre, memoize, memoize_key=None)` | internal base | Handles copying, chaining, memoization, and `reset_cache()` |
| `Mapper` | `Mapper(name, field_names=None, mapped_field_names=None, pre=None, memoize=False, memoize_key=None)` | `DataPoint` or `None` | Pulls fields from the input object, calls `run(**kwargs)`, and writes mapped fields back onto the copied object |
| `LambdaMapper` | `LambdaMapper(name, f, pre=None, memoize=False, memoize_key=None)` | `DataPoint` or `None` | Wraps a direct transform function that receives the copied input |
| `lambda_mapper` | `lambda_mapper(name=None, pre=None, memoize=False, memoize_key=None)` | decorator factory | Use as `@lambda_mapper()`; missing parentheses raises a `ValueError` |

### Mapper notes

- If `field_names=None`, `Mapper` infers input attributes from `run` parameter names.
- `mapped_field_names` renames the keys returned by `run` before they are attached to the data point.
- `pre` runs before the main mapper.
- The built-in copy step uses a pickle round-trip, so returned objects should be picklable enough for that path.
- `BaseMapper.__call__` caches `None` results too.

## Preprocessors

| Symbol | Signature | Return | Notes |
| --- | --- | --- | --- |
| `BasePreprocessor` | alias of `BaseMapper` | internal base | Same copy/memoize semantics as the mapper base |
| `Preprocessor` | `Preprocessor(name, field_names=None, mapped_field_names=None, pre=None, memoize=False, memoize_key=None)` | `DataPoint` or `None` | Mapper-style transform with preprocessing vocabulary |
| `LambdaPreprocessor` | `LambdaPreprocessor(name, f, pre=None, memoize=False, memoize_key=None)` | `DataPoint` or `None` | Direct transform function for preprocessing |
| `preprocessor` | `preprocessor(name=None, pre=None, memoize=False, memoize_key=None)` | decorator factory | Same calling rules as `lambda_mapper` |
| `SpacyPreprocessor` | `SpacyPreprocessor(text_field, doc_field, language='en_core_web_sm', disable=None, pre=None, memoize=False, memoize_key=None, gpu=False)` | `DataPoint` or `None` | Loads a spaCy pipeline, adds a `Doc` field, and can prefer GPU via `spacy.prefer_gpu()` |

### Preprocessor notes

- `SpacyPreprocessor` loads the model at construction time.
- `doc_field` receives the spaCy `Doc` object; other doc attributes stay inside that object.
- Use `pre` to chain a text normalizer before spaCy parsing.
- Memoization is especially useful when multiple downstream consumers reuse the same parsed document.

## Spark wrappers

| Symbol | Signature | Return | Notes |
| --- | --- | --- | --- |
| `make_spark_mapper` | `make_spark_mapper(mapper)` | same mapper object | Patches a mapper so `pyspark.sql.Row` inputs are rebuilt instead of mutated in place |
| `make_spark_preprocessor` | `make_spark_preprocessor(preprocessor)` | same preprocessor object | Alias of `make_spark_mapper`; use it for `Preprocessor` instances |

### Spark notes

- `Row` objects are immutable, so Spark transforms must rebuild the row from a dict of fields.
- Use these wrappers for `Mapper` / `Preprocessor` objects, not for LF or SF logic.
- Local Spark checks require PySpark importability; starting a real Spark job also requires a working Java runtime.

## Augmentation APIs

| Symbol | Signature | Return | Notes |
| --- | --- | --- | --- |
| `TransformationFunction` | `TransformationFunction(name, field_names=None, mapped_field_names=None, pre=None, memoize=False, memoize_key=None)` | `DataPoint` or `None` | TF-specific mapper used by augmentation |
| `transformation_function` | `transformation_function(name=None, pre=None, memoize=False, memoize_key=None)` | decorator factory | Use as `@transformation_function()` |
| `TFApplier` | `TFApplier(tfs, policy)` | applier | Applies TF sequences to a list of data points |
| `PandasTFApplier` | `PandasTFApplier(tfs, policy)` | applier | Applies TF sequences to a `pandas.DataFrame` |

### Augmentation notes

- TF names must be unique when the applier is constructed.
- `keep_original=True` adds an empty sequence before transformed copies.
- When a TF returns `None`, that transformed copy is dropped.
- `PandasTFApplier` preserves the original row index values in the augmented output, which can produce repeated indices.
- `TFApplier.apply` returns a list of transformed data points; `PandasTFApplier.apply` returns a `DataFrame`.

## Policies

| Symbol | Signature | Return | Notes |
| --- | --- | --- | --- |
| `ApplyAllPolicy` | `ApplyAllPolicy(n_tfs, n_per_original=1, keep_original=True)` | policy | Generates `list(range(n_tfs))` every time |
| `ApplyOnePolicy` | `ApplyOnePolicy(n_per_original=1, keep_original=True)` | policy | Convenience policy for one TF |
| `ApplyEachPolicy` | `ApplyEachPolicy(n_tfs, keep_original=True)` | policy | Generates one singleton sequence per TF |
| `MeanFieldPolicy` | `MeanFieldPolicy(n_tfs, sequence_length=1, p=None, n_per_original=1, keep_original=True)` | policy | Samples TF indices from a distribution |
| `RandomPolicy` | `RandomPolicy(n_tfs, sequence_length=1, n_per_original=1, keep_original=True)` | policy | Uniform `MeanFieldPolicy` baseline |

### Policy notes

- `generate_for_example()` prepends `[]` when `keep_original=True`.
- `n_per_original` controls how many transformed sequences are generated per input example.
- `MeanFieldPolicy.p` must be a valid distribution of length `n_tfs`.

## Synthetic helper

| Symbol | Signature | Return | Notes |
| --- | --- | --- | --- |
| `generate_simple_label_matrix` | `generate_simple_label_matrix(n, m, cardinality, abstain_multiplier=1.0)` | `(P, Y, L)` | Builds a synthetic LF probability table, true labels, and a label matrix for label-model experiments |

### Synthetic notes

- `P` has shape `(m, cardinality + 1, cardinality)`.
- `Y` has shape `(n,)` and is sampled from balanced classes.
- `L` has shape `(n, m)` and encodes abstain as `-1`.
- Increase `abstain_multiplier` to make sparse label matrices more likely.
