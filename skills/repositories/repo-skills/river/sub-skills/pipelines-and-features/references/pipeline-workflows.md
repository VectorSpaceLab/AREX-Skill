# Pipeline workflows

## Construction patterns

- `a | b | c` builds a sequential pipeline.
- `a + b` builds a `TransformerUnion` that merges branch outputs.
- `a * b` builds a `TransformerProduct` when both sides are transformers.
- `transformer * "group"` or `transformer * ["g1", "g2"]` builds a `Grouper` that keeps a
  separate copy of the transformer per group key.
- Bare callables are automatically wrapped in `compose.FuncTransformer`.
- Lists passed into a pipeline or union are treated as collections of steps.
- Explicit names use `(name, step)` tuples and are worth using whenever you plan to inspect a step
  later.

A compact mixed-schema pattern is:

```python
import numbers
from river import compose, feature_extraction, linear_model, preprocessing

numeric = compose.SelectType(numbers.Number) | preprocessing.StandardScaler()
text = compose.Select("text") | feature_extraction.TFIDF(on="text")

features = compose.TransformerUnion(
    ("numeric", numeric),
    ("text", text),
)

model = compose.Pipeline(
    ("features", features),
    ("model", linear_model.LogisticRegression()),
)
```

If you want both bag-of-words and TF-IDF from the same text field, prefix one branch and combine
it with the other so feature names do not collide.

## Learning order

River pipelines learn in a predictable order.

### `learn_one`

- Unsupervised intermediate transformers learn before they transform the input.
- Supervised transformers learn after the branch has produced transformed features, so they can
  use the original `x` and `y` without leakage.
- The final estimator learns last.

### `learn_during_predict`

`compose.learn_during_predict()` changes the learning order for unsupervised steps during
prediction:

- Unsupervised steps can update during `predict_one`, `predict_proba_one`, `score_one`, and
  `transform_one`.
- Supervised steps still wait for `learn_one`.
- The final estimator still only receives a prediction call unless the step itself declares a
  training method that the pipeline can route to.

Use this mode only when you really want online preprocessing to advance during inference.

## Parameter routing

The pipeline inspects method signatures once and forwards only the extras each step declares.
That means:

- `t=` is routed to steps such as `feature_extraction.Agg`, `TargetAgg`, and the wrapped object
  inside `utils.TimeRolling` when they accept it.
- `w=` is routed to estimators that declare sample weight, such as linear models.
- Unknown keyword arguments are dropped for steps that do not accept them.
- A method with `**kwargs` receives every extra argument.

The same routing applies to predict-time calls when `learn_during_predict` is active.

## Debugging the flow

- `debug_one(x)` shows how a sample changes at each step.
- `debug_one` only inspects the current state; it does not train the pipeline.
- `utils.log_method_calls` is useful when you want to see which methods were actually called
  during a prediction or update.

A typical inspection loop is:

```python
import io
import logging
from river import compose, utils

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logs = io.StringIO()
handler = logging.StreamHandler(logs)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

with utils.log_method_calls(), compose.learn_during_predict():
    model.predict_one(x, t=t)

print(logs.getvalue())
```

## Mini-batch behavior

When a step implements `learn_many` / `transform_many` / `predict_many`, prefer them for data
that already lives in a dataframe or series. Batch support is especially useful for text
vectorizers and preprocessing steps.

Good batch habits:

- Keep the batch object backend-native.
- Prefer `transform_many` and `learn_many` only when the whole branch supports them.
- Fall back to row-by-row calls when a step is online-only.
- Use `learn_one` / `transform_one` if you need precise control over `t` or other routed extras.

## Small patterns to reuse

### Text plus numeric branches

```python
import numbers

from river import compose, feature_extraction, linear_model, preprocessing

numeric = compose.SelectType(numbers.Number) | preprocessing.StandardScaler()
text = compose.Select("text") | feature_extraction.BagOfWords(on="text")
model = (numeric + text) | linear_model.LogisticRegression()
```

### Interaction terms

```python
pairwise = compose.Select("a", "b") * compose.Select("x", "y")
```

### Grouped transformers

```python
weather_imputer = preprocessing.StatImputer(("temperature", stats.Mean())) * "weather"
```

### Rolling feature flow

```python
import datetime as dt

agg = feature_extraction.Agg(
    on="value",
    by="group",
    how=utils.TimeRolling(stats.Mean, period=dt.timedelta(days=7)),
)
```
