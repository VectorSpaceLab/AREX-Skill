# Troubleshooting

## Duplicate step names

**Symptom:** a pipeline prints names like `StandardScaler1` or `Agg1`, or a later step is hard to
retrieve by name.

**Cause:** `Pipeline` and `TransformerUnion` auto-suffix duplicate step names.

**Fix:** give the step an explicit name with a `(name, step)` tuple if you want a stable handle:

```python
model = compose.Pipeline(
    ("scale", preprocessing.StandardScaler()),
    ("model", linear_model.LogisticRegression()),
)
```

## Wrong feature selection

**Symptom:** a branch is empty, a downstream model sees too few features, or a key error appears
when selecting features.

**Cause:** `Select` only keeps the keys you list, and `Discard` removes the keys you list.
`SelectType` is safer when the schema changes or when you mix numeric and text values.

**Fix:** inspect the actual keys with `debug_one`, then narrow the selector or switch to
`SelectType`.

## Text and numeric mixing

**Symptom:** a text transform feeds strings into a numeric scaler, or a numeric branch receives the
text field.

**Cause:** text vectorizers and numeric preprocessors expect different input shapes.

**Fix:** split the branches and merge them afterwards.

```python
import numbers

from river import compose, feature_extraction, linear_model, preprocessing

numeric = compose.SelectType(numbers.Number) | preprocessing.StandardScaler()
text = compose.Select("text") | feature_extraction.TFIDF(on="text")
model = (numeric + text) | linear_model.LogisticRegression()
```

If two text branches emit the same token names, prefix or rename them before the union.

## Target aggregation and timestamps

**Symptom:** a rolling aggregate does not change, or a timestamp seems to leak into the final
estimator.

**Cause:** `Agg` and `TargetAgg` only use `t` when their `how` object supports it, such as
`utils.TimeRolling`. The timestamp must be passed through the pipeline call, not copied into the
feature dict.

**Fix:** call the pipeline with `t=` on both `learn_one` and, when relevant,
`predict_one` inside `compose.learn_during_predict()`.

## `learn_during_predict` surprises

**Symptom:** a scaler or other unsupervised step changes during prediction, or the model state seems
to advance before `learn_one`.

**Cause:** the `compose.learn_during_predict()` context manager intentionally lets unsupervised
steps learn during predict-time calls.

**Fix:** only use the context when you want predict-time preprocessing updates. Leave it off for
normal online learning.

Remember that `debug_one` does not train the pipeline; it only shows the current state.

## Missing pandas for mini-batch

**Symptom:** a batch example fails when you pass a dataframe or series.

**Cause:** the example or the chosen backend is not available in your environment. If the
example uses pandas DataFrames or Series, pandas itself is missing.

**Fix:**

- Install pandas if the example uses `pd.DataFrame` or `pd.Series`.
- Or switch to another supported eager backend.
- Or fall back to `learn_one` / `transform_one`.

If a branch only implements online methods, keep the whole flow in online mode.

## Unexpected feature keys

**Symptom:** the feature names in `debug_one` or `transform_one` do not match what you expected.

**Cause:** unions merge branch outputs, products concatenate names with `*`, and text/vector
transforms generate their own token names.

**Fix:**

- Use `Prefixer`, `Suffixer`, or `Renamer` to disambiguate branches.
- Use `debug_one` to inspect the actual keys.
- Check that a `Select` branch still contains the expected source key before the next transform.
- Avoid mutating the same input dict in multiple branches.

## `FuncTransformer` side effects

**Symptom:** a custom function seems to change another branch's input.

**Cause:** the function mutates the input dict instead of returning a fresh one.

**Fix:** copy the input first or return a new dict. River assumes transformers are pure unless you
explicitly manage the mutation yourself.
