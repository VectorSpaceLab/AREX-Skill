# Feature engineering

## Preprocessing

Use `preprocessing` when you want to clean or normalize existing values before a model sees them.
Common choices include:

- `StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`, `RobustScaler`, `Normalizer`
- `OneHotEncoder`, `OrdinalEncoder`, `FeatureHasher`
- `PreviousImputer`, `StatImputer`
- `PredClipper`, `TargetStandardScaler`, `TargetMinMaxScaler`
- `GapEncoder`, `LDA`, `GaussianRandomProjector`, `SparseRandomProjector`

Typical use:

```python
import numbers

from river import compose, preprocessing

num = compose.SelectType(numbers.Number) | preprocessing.StandardScaler()
cat = compose.SelectType(str) | preprocessing.OneHotEncoder()
```

When you need grouped imputation, wrap the imputer with a group key:

```python
from river import preprocessing, stats

weather_imputer = preprocessing.StatImputer(("temperature", stats.Mean())) * "weather"
```

## Text features

`feature_extraction.BagOfWords` and `feature_extraction.TFIDF` convert text into token-based
feature dictionaries. They can read:

- a raw text string, or
- a dictionary plus `on="field_name"`.

Useful habits:

- Use `BagOfWords` for counts.
- Use `TFIDF` when you want document-frequency weighting.
- Use `on=` when the text lives inside a larger feature dict.
- Prefix text branches if more than one text extractor could emit the same token names.

Example:

```python
from river import compose, feature_extraction

text = compose.Select("text") | feature_extraction.TFIDF(on="text")
```

## Streaming aggregates

`feature_extraction.Agg` computes a feature aggregate; `TargetAgg` computes a target aggregate.
Both are built on top of running statistics from `stats` and can be grouped by one or more keys.

Common combinations:

- `stats.Mean`, `stats.Count`, `stats.Max`, `stats.Min`
- `stats.EWMean`, `stats.EWVar` for recency weighting
- `stats.BayesianMean` when you want a prior for target encoding
- `stats.Shift` when you want lag features

Rolling windows are usually built with `utils.Rolling` or `utils.TimeRolling`:

```python
import datetime as dt
from river import feature_extraction, stats, utils

agg = feature_extraction.Agg(
    on="value",
    by=["group", "hour"],
    how=utils.TimeRolling(stats.Mean, period=dt.timedelta(days=7)),
)

target = feature_extraction.TargetAgg(
    by="store_id",
    how=utils.Rolling(stats.Mean, window_size=14),
)
```

Use the class plus constructor kwargs style, not a pre-built instance. For example,
`utils.Rolling(stats.Mean, window_size=7)` is the preferred form.

### Safe pattern for target encoding

```python
from river import feature_extraction, stats, utils

encoder = feature_extraction.TargetAgg(
    by="place",
    how=stats.BayesianMean(prior=3, prior_weight=1),
)
```

## Branching and interactions

Use `compose.Select`, `Discard`, `SelectType`, `FuncTransformer`, `TransformerUnion`,
`TransformerProduct`, and `Grouper` to shape feature flow.

- `Select` keeps only chosen keys.
- `Discard` removes chosen keys.
- `SelectType` keeps values by runtime type.
- `FuncTransformer` wraps a custom function that takes a dict and returns a dict.
- `TransformerUnion` merges parallel branches.
- `TransformerProduct` multiplies branch outputs into interaction terms.
- `Grouper` keeps a separate transformer per group key.

Example patterns:

```python
from river import compose

pairwise = compose.Select("a", "b") * compose.Select("x", "y")
```

```python
from river import compose, feature_extraction

# Custom feature function, written to return a fresh dict.
def add_time_features(x):
    return {**x, "hour": x["moment"].hour, "weekday": x["moment"].weekday()}

model = compose.FuncTransformer(add_time_features) | feature_extraction.PolynomialExtender()
```

## Feature selection

`feature_selection` is for removing or keeping features after they have been created.
The usual tools are:

- `VarianceThreshold` for unsupervised pruning
- `SelectKBest` for supervised ranking
- `PoissonInclusion` for random inclusion in very wide sparse problems

Place feature selection after feature creation and before the final estimator.

## Sketches

`sketch` objects are not pipeline transformers. They are bounded-memory summaries that help when
you want to inspect a live stream without storing everything.

Useful sketches include:

- `Histogram` for approximate distributions
- `Counter` for count-min estimates
- `HeavyHitters` for frequent items
- `NUnique` for approximate cardinality
- `Set` for approximate membership

Use sketches when you want monitoring or exploratory summaries, not when you need a model
feature.

## Feature dictionary hygiene

Good feature dict habits prevent confusing pipeline bugs:

- Return a new dict from custom transformers.
- Avoid mutating shared input dicts in place.
- Prefix or rename branch outputs before merging similar branches.
- Keep key names stable so downstream `Select` / `Discard` steps remain predictable.
- If two branches can emit the same key, rename them before the union or product step.

A practical mixed text + numeric pattern is:

```python
import numbers

from river import compose, feature_extraction, linear_model, preprocessing

numeric = compose.SelectType(numbers.Number) | preprocessing.StandardScaler()
text = compose.Select("text") | feature_extraction.BagOfWords(on="text")
model = (numeric + text) | linear_model.LogisticRegression()
```

## Mini-batch guidance

Use `learn_many` and `transform_many` when the step supports them and you already have a dataframe
or series. Use row-by-row methods when you need per-event control, timestamps, or a step that does
not expose batch methods.

Batch reminders:

- `BagOfWords` and `TFIDF` support mini-batch processing.
- `Select` and `TransformerUnion` also support batch methods.
- If a branch only has online methods, keep the whole flow in online mode.
- If you pass pandas objects, pandas must be installed; otherwise use another supported eager
  backend or switch to one-row methods.
