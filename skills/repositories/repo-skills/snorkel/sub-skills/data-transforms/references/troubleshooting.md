# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Object ... has no hashing proxy.` | The default memoization key cannot hash one of the input fields. | Pass a custom `memoize_key`, reduce the key to a stable field such as `uid`, or disable memoization. |
| `ValueError: Looks like this decorator is missing parentheses!` | `@lambda_mapper`, `@preprocessor`, or `@transformation_function` was used without `()`. | Call the decorator factory: `@lambda_mapper()` and friends. |
| `ValueError: Operator names not unique ...` | Two TFs share the same `name`. | Rename the TFs so every transform in the applier has a unique name. |
| A mapper appears to mutate the source object | The transform was written as if the original object were being edited in place. | Remember that the base class copies inputs before running the transform; return the mutated copy and do not rely on source mutation. |
| Nested mutable fields seem to change unexpectedly | The copied object is the one being mutated, not the original reference. | Treat the returned object as the only mutated result and verify the source object after the call if you need to confirm copy safety. |
| A mapper returns `None` and the output row disappears | The transform chose to drop that transformed copy. | Return the data point when you want to keep it, or keep the original with `keep_original=True`. |
| The augmented Pandas output has repeated indices | Augmentation keeps the source row index on repeated examples. | Call `reset_index(drop=True)` after augmentation if you need a fresh index. |
| `SpacyPreprocessor` fails at construction | The requested spaCy model is unavailable. | Install an available model or choose a language string that exists in the environment. |
| Spark code fails on `Row` mutation | `Row` objects are immutable. | Use `make_spark_mapper` or `make_spark_preprocessor` so the object is rebuilt from a field dict. |
| Spark wrappers import but real Spark work fails | Local Java or PySpark is missing or mismatched. | Verify a local PySpark installation and a working Java runtime before running a real Spark job. |
| `Mapper.run` cannot accept `*args` or `**kwargs` | The mapper signature is too loose for field inference. | Use fixed parameter names only. |

## Quick recovery checklist

1. Check whether the input is hashable enough for memoization.
2. Check whether the object should be copied instead of mutated.
3. Check whether the output is being dropped by `None`.
4. Check whether the row index is being preserved by augmentation.
5. Check whether spaCy or PySpark is actually installed before treating the failure as a code bug.
