# Vaex ML workflows

This reference gives concrete patterns for building Vaex ML preprocessing and
model-integration workflows without opening source docs.

## Minimum imports

```python
import vaex
import vaex.ml

# Required for the scikit-learn wrappers; do not rely on implicit imports.
import vaex.ml.sklearn
from vaex.ml.sklearn import Predictor, IncrementalPredictor

# Required for the KMeans class location.
import vaex.ml.cluster
from vaex.ml.cluster import KMeans
```

Optional estimator wrappers live in their own modules, for example
`vaex.ml.xgboost`, `vaex.ml.lightgbm`, `vaex.ml.catboost`,
`vaex.ml.tensorflow`, and `vaex.ml.incubator.*`. Import those modules only when
the corresponding optional package is installed.

## Train/test split pattern

`df.ml.train_test_split(test_size=0.2, strings=True, virtual=True,
verbose=True)` returns shallow Vaex DataFrame copies. The split is ordered: the
first fraction becomes the test set and the remainder becomes the train set.
It does not randomize rows.

```python
import vaex
import vaex.ml

# Use a shuffled on-disk dataset for large ordered data, or an in-memory shuffle
# for small data that safely fits the user's memory budget.
df = df.shuffle(random_state=31)       # small-data convenience
# For large data, prefer: df.shuffle().export("shuffled.hdf5"); df = vaex.open("shuffled.hdf5")

train, test = df.ml.train_test_split(test_size=0.2, verbose=False)
```

Fit every target-aware transformer and model on `train`, never on `test`.
For shuffled on-disk production workflows, keep the shuffled file path under the
user's project or data directory; do not rely on a checkout-specific file.

## Numerical preprocessing

All Vaex ML transformers follow the scikit-learn-style pattern:

```python
scaler = vaex.ml.StandardScaler(features=["age", "fare"], prefix="scaled_")
train_scaled = scaler.fit_transform(train)
test_scaled = scaler.transform(test)
```

Useful numerical transformers:

- `vaex.ml.StandardScaler`: removes mean and/or divides by standard deviation;
  defaults to prefix `standard_scaled_`.
- `vaex.ml.MinMaxScaler`: maps values into `feature_range`, default `(0, 1)`;
  defaults to prefix `minmax_scaled_`.
- `vaex.ml.MaxAbsScaler`: divides by maximum absolute value; defaults to prefix
  `absmax_scaled_`.
- `vaex.ml.RobustScaler`: centers by approximate median and scales by a
  percentile range, default `(25, 75)`; defaults to prefix `robust_scaled_`.

The returned DataFrame is a shallow copy with virtual transformed columns. Use
`get_column_names(regex=...)` to select generated feature columns for later
models.

```python
train_scaled = vaex.ml.StandardScaler(features=["x", "y"], prefix="scaled_").fit_transform(train)
scaled_features = train_scaled.get_column_names(regex="^scaled_")
```

## Categorical, cyclical, grouped, and binned features

Use these when the transformation itself should be reusable across train/test or
production data. For one-off expression/groupby feature engineering, route to
[../../expressions-analytics/SKILL.md](../../expressions-analytics/SKILL.md).

```python
label = vaex.ml.LabelEncoder(features=["sex", "embarked"], allow_unseen=True)
train_labeled = label.fit_transform(train)
test_labeled = label.transform(test)

onehot = vaex.ml.OneHotEncoder(features=["deck"], prefix="deck_")
train_hot = onehot.fit_transform(train_labeled)

grouped = vaex.ml.GroupByTransformer(
    by="customer_id",
    agg={"mean_amount": vaex.agg.mean("amount"), "n_rows": vaex.agg.count()},
    rsuffix="_group",
)
train_grouped = grouped.fit_transform(train)
test_grouped = grouped.transform(test)
```

Transformer choices:

- `LabelEncoder`: ordinal integer labels. Set `allow_unseen=True` when test or
  production data may contain unseen categories; unseen values become `-1`.
- `OneHotEncoder`: one virtual column per category; avoid high-cardinality
  columns unless column expansion is acceptable.
- `MultiHotEncoder`: binary-code columns from ordinal-encoded categories; useful
  when one-hot cardinality is too large but a categorical split is still needed.
- `FrequencyEncoder`: maps categories to observed train frequency; `unseen` can
  be `"nan"` or `"zero"`.
- `BayesianTargetEncoder`: smoothed target mean per category. Fit only on train
  data to avoid leakage; `weight` controls smoothing toward the global target
  mean.
- `WeightOfEvidenceEncoder`: target must be binary `0/1` or boolean-like; use
  `epsilon` to avoid division by zero.
- `CycleTransformer`: encodes cycles, for example day-of-week or hour-of-day,
  into sine/cosine components. Set `n` to the period.
- `GroupByTransformer`: computes grouped aggregates on fit data, then maps them
  onto compatible DataFrames. This is the reusable ML form of groupby-derived
  features.
- `KBinsDiscretizer`: bins continuous columns with `strategy="uniform"`,
  `"quantile"`, or `"kmeans"`.

## Dimensionality reduction and projection

```python
features = ["sepal_width", "petal_length", "sepal_length", "petal_width"]
pca = vaex.ml.PCA(features=features, n_components=2, prefix="PCA_")
train_pca = pca.fit_transform(train)
test_pca = pca.transform(test)
```

- `vaex.ml.PCA` fits from Vaex covariance/mean calculations and adds virtual
  columns named by `prefix` plus component index. It requires at least two input
  features and `n_components <= len(features)`.
- `vaex.ml.PCAIncremental` wraps scikit-learn's incremental PCA during `fit` and
  is useful for wide feature sets. Set `batch_size` to control per-batch memory.
- `vaex.ml.RandomProjections` wraps scikit-learn random projections during `fit`;
  choose `matrix_type="gaussian"` or `"sparse"`.

## KMeans clustering

The class is in `vaex.ml.cluster`, not the top-level `vaex.ml` namespace.

```python
import vaex.ml.cluster

features = ["x", "y"]
kmeans = vaex.ml.cluster.KMeans(
    features=features,
    n_clusters=3,
    init="random",
    random_state=42,
    max_iter=25,
    prediction_label="cluster_id",
)
kmeans.fit(train)
train_clustered = kmeans.transform(train)
test_clustered = kmeans.transform(test)
```

`transform` adds a lazy virtual prediction column. First use can trigger Numba
compilation overhead. Keep the backend expectation CPU-only.

## Scikit-learn Predictor with lazy prediction column

Use `Predictor` when the underlying estimator implements a normal scikit-learn
`fit(X, y)` and prediction method. `fit` and `predict` copy selected Vaex
features into memory. `transform` adds a lazy virtual column whose values are
computed when evaluated.

```python
import vaex.ml.sklearn
from vaex.ml.sklearn import Predictor
from sklearn.linear_model import LinearRegression

features = ["scaled_x", "scaled_y"]
model = Predictor(
    model=LinearRegression(),
    features=features,
    target="target",
    prediction_name="prediction",
)
model.fit(train_scaled)               # copies train_scaled[features] to memory
pred_array = model.predict(test_scaled)  # returns an in-memory numpy array
test_pred = model.transform(test_scaled) # adds lazy virtual column "prediction"
```

`prediction_type` can be `"predict"`, `"predict_proba"`, or
`"predict_log_proba"`; the wrapped estimator must implement the chosen method.
Probability predictions may be 2-D arrays.

## IncrementalPredictor for partial-fit estimators

Use `IncrementalPredictor` for estimators with `.partial_fit(...)`, such as many
online scikit-learn models. It evaluates only one Vaex batch at a time during
fit.

```python
from sklearn.linear_model import SGDRegressor
from vaex.ml.sklearn import IncrementalPredictor

incremental = IncrementalPredictor(
    model=SGDRegressor(random_state=42),
    features=features,
    target="target",
    batch_size=100_000,
    num_epochs=3,
    shuffle=True,
    prediction_name="pred_target",
)
incremental.fit(train_scaled)
test_pred = incremental.transform(test_scaled)
```

For classifiers, pass required `partial_fit` keyword arguments such as
`partial_fit_kwargs={"classes": [0, 1, 2]}`.

## State transfer and Pipeline save/load

Vaex DataFrames carry serializable state for virtual columns, functions,
selections, and ML transformation metadata. Use `df.ml.state_transfer()` when a
training DataFrame has accumulated virtual preprocessing columns that should be
reapplied to a compatible test or production DataFrame.

```python
train["r"] = (train.x**2 + train.y**2) ** 0.5
pca = vaex.ml.PCA(features=["r", "z"], n_components=2)
train_pca = pca.fit_transform(train)
state_transfer = train_pca.ml.state_transfer()

test_pca = state_transfer.transform(test)  # test must contain base columns x, y, z
```

`vaex.ml.Pipeline` is list-like. Its `transform(dataframe)` applies every object
in order. Its `predict(dataframe)` applies all but the last object as
transformers, then calls the last object's `predict`.

```python
from pathlib import Path
from sklearn.linear_model import LinearRegression
from vaex.ml.sklearn import Predictor

state_transfer = train_scaled.ml.state_transfer()
model = Predictor(
    model=LinearRegression(),
    features=["scaled_x", "scaled_y"],
    target="target",
    prediction_name="pred",
)
model.fit(train_scaled)

pipeline = vaex.ml.Pipeline([state_transfer, model])
pipeline.save("ml_pipeline.json")

loaded = vaex.ml.Pipeline()
loaded.load("ml_pipeline.json")
scored = loaded.transform(test)        # includes scaled_x, scaled_y, pred
pred = loaded.predict(test)            # numpy prediction array
```

Save to a path whose parent directory already exists. Load only trusted pipeline
files because estimator state may be serialized inside them.

## Optional estimator integrations

Vaex ML includes wrapper modules for several optional packages. These are CPU
package integrations unless the optional library itself is configured otherwise;
this sub-skill does not verify or claim GPU support.

- `vaex.ml.xgboost.XGBoostModel`: requires `xgboost`; supports validation sets,
  early stopping, and `evals_result` similar to `xgboost.train`.
- `vaex.ml.lightgbm.LightGBMModel`: requires `lightgbm`; supports validation
  sets and LightGBM callbacks through wrapper arguments.
- `vaex.ml.catboost.CatBoostModel`: requires `catboost`; supports
  `prediction_type`, optional batch training, and model summing.
- `vaex.ml.tensorflow`: optional TensorFlow extra. `df.ml.tensorflow` can expose
  Keras generator helpers and `KerasModel` when TensorFlow is installed, but this
  path is optional and unverified here.
- `vaex.ml.incubator.river`, `vaex.ml.incubator.annoy`, and
  `vaex.ml.incubator.pygbm`: incubator integrations; verify package availability
  and APIs before relying on them.
