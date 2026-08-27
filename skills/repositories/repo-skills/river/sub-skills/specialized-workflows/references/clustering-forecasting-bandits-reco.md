# Clustering, Forecasting, Bandits, Recommenders, Sampling, and Distributions

## Clustering loops and metrics

Clusterers are unsupervised estimators. Their `learn_one` consumes only `x`, and `predict_one` returns a cluster ID.

```python
from river import cluster, metrics

model = cluster.KMeans(n_clusters=3, halflife=0.4, seed=0)
metric = metrics.Silhouette()

for x in stream_of_feature_dicts:
    model.learn_one(x)
    y_pred = model.predict_one(x)
    metric.update(x, y_pred, model.centers)
```

Choose the clusterer by stream shape:

- `cluster.KMeans`: simple incremental centroid tracking; scale numeric data appropriately.
- `cluster.CluStream`, `cluster.DBSTREAM`, and `cluster.DenStream`: micro-cluster algorithms for evolving streams and later macro-cluster generation.
- `cluster.STREAMKMeans`: chunked stream clustering with incremental KMeans over chunk summaries.
- `cluster.TextClust`: text stream clustering after text feature extraction.
- `cluster.ODAC`: hierarchical clustering for multivariate time-series-like streams; it tracks structure changes rather than producing ordinary labels for every point.

Metric choice:

- Internal clustering metrics do not require ground-truth labels. `metrics.Silhouette` requires `x`, `y_pred`, and current `centers`; lower is better for River's online ratio implementation.
- External clustering metrics require labels. Use `metrics.Rand`, `metrics.AdjustedRand`, `metrics.Homogeneity`, `metrics.Completeness`, or `metrics.VBeta` when the stream has known cluster labels.
- Micro-cluster algorithms may distinguish learned micro-clusters from derived macro-clusters. Use the public `centers`, `clusters`, or `micro_clusters` attributes according to the metric and reporting objective.

## Forecasting and horizon metrics

River forecasters use a time-series-specific API:

```python
model.learn_one(y, x=None)
y_pred = model.forecast(horizon=12, xs=future_xs)
```

Core forecasters:

- `time_series.HoltWinters`: online exponential smoothing with optional trend, seasonality, and multiplicative seasonality.
- `time_series.SNARIMAX`: online seasonal/nonlinear ARIMA-style forecaster with optional autoregressive, differencing, moving-average, seasonal, and exogenous-feature components.

Evaluation uses horizon-aware metrics rather than ordinary one-step supervised metrics:

```python
from river import evaluate, metrics, time_series

metric = evaluate.evaluate(
    dataset=time_series_stream,
    model=time_series.HoltWinters(alpha=0.3),
    metric=metrics.MAE(),
    horizon=4,
)
```

Rules:

- `forecast(horizon, xs=None)` must return exactly `horizon` predictions.
- If `xs` is supplied, its length must equal `horizon`; each future feature dict must contain only features available at forecast time.
- `evaluate.iter_evaluate` yields `(x, y, y_pred, horizon_metric)` at each evaluation step.
- `evaluate.evaluate` returns `time_series.HorizonMetric` by default, with one metric value per horizon step.
- Pass `agg_func` to get `time_series.HorizonAggMetric`, which aggregates the per-horizon values with a function such as `statistics.mean`.
- For ordinary one-step regression on a delayed target, route to the shared streaming-evaluation workflow instead of using a forecaster API.

## Bandit policy loops without Gym

Bandit policies do not require a Gym environment. The core loop is direct:

```python
from river import bandit

policy = bandit.EpsilonGreedy(epsilon=0.1, burn_in=1)
arms = ["A", "B", "C"]

arm = policy.pull(arms)
reward = observe_reward(arm)
policy.update(arm, reward)
```

For contextual policies, pass context to both `pull` and `update`:

```python
arm = contextual_policy.pull(arms, context=x)
contextual_policy.update(arm, x, reward)
```

Policy concepts:

- `reward_obj` can be a statistic, metric, or probability distribution. `stats.Mean`, `stats.Sum`, `proba.Beta`, and rolling wrappers are common choices.
- `burn_in` ensures every arm can be tried before exploitation dominates.
- `policy.ranking` sorts arms by current reward object state.
- `bandit.evaluate` benchmarks policies on a Gym-style environment when such an environment is installed, but it is optional.

Offline replay uses logged history and does not need Gym:

```python
from river import bandit

history = [
    (["A", "B"], None, "A", 1.0),
    (["A", "B"], None, "B", 0.0),
]
reward_stat, n_used = bandit.evaluate_offline(
    policy=bandit.EpsilonGreedy(epsilon=0.0),
    history=history,
)
```

Each history item is `(arms_available, context, arm_that_was_pulled, reward)`. Replay only updates the policy when the policy's chosen arm matches the historical arm. `n_used` is therefore usually smaller than the number of log rows.

## Recommendation and ranking

`reco` models inherit from `reco.base.Ranker` and use explicit user and item IDs rather than a single feature dict.

```python
from river import reco

model = reco.Baseline()
model.learn_one(user="alice", item="politics", y=1.0)
score = model.predict_one(user="alice", item="sports")
ranking = model.rank(user="alice", items={"politics", "sports", "music"})
```

Model choices:

- `reco.RandomNormal`: dummy stochastic ranker for baselines.
- `reco.Baseline`: global mean plus user/item bias.
- `reco.FunkMF`: latent user/item matrix factorization.
- `reco.BiasedMF`: matrix factorization with global/user/item biases.

Use stable hashable IDs for users and items. `rank(user, items, x=None)` sorts the candidate set by predicted preference; it does not retrieve candidates for you. If preferences depend on context, pass the same context to `rank`, `predict_one`, and `learn_one`, and check `model.is_contextual` before assuming the model uses it.

## Factorization machines for recommendation and CTR

Use `facto` when the task is better expressed as feature interactions rather than explicit `reco` user/item rankers. This is common for CTR, ads, sparse categorical features, and user/item/context interaction features.

Model families:

- `facto.FMClassifier` and `facto.FMRegressor`: pairwise feature interactions.
- `facto.FFMClassifier` and `facto.FFMRegressor`: field-aware interactions; field names are inferred from the feature name prefix before the first underscore.
- `facto.FwFMClassifier` and `facto.FwFMRegressor`: field-weighted interactions.
- `facto.HOFMClassifier` and `facto.HOFMRegressor`: higher-order interactions up to a chosen degree.

Practical rules:

- String features are automatically one-hot encoded as categorical variables.
- Numeric features participate directly in interactions; scale or normalize them when magnitudes differ widely.
- `sample_normalization=True` can help when sparse sample norms vary strongly.
- `debug_one(x)` explains unary, interaction, and intercept contributions for a sample.
- Use classifier variants for click/no-click or conversion tasks and regressor variants for ratings or value prediction.

## Imbalanced learning wrappers

`imblearn` wrappers modify which samples the wrapped estimator sees during `learn_one`.

Classification stream wrappers:

- `imblearn.RandomOverSampler(classifier, desired_dist, seed=None)` over-samples minority classes.
- `imblearn.RandomUnderSampler(classifier, desired_dist, seed=None)` under-samples majority classes.
- `imblearn.RandomSampler(classifier, desired_dist, sampling_rate, seed=None)` mixes over- and under-sampling.
- `imblearn.HardSamplingClassifier(classifier, size, p, loss=None, seed=None)` replays hard classification examples from a bounded buffer.

Regression stream wrappers:

- `imblearn.ChebyshevOverSampler(regressor)` and `imblearn.ChebyshevUnderSampler(regressor, sp=0.15, seed=None)` bias training toward rare target values.
- `imblearn.HardSamplingRegressor(regressor, size, p, loss=None, seed=None)` replays hard regression examples.

Sampling placement determines which state is affected. Wrap the classifier/regressor pipeline if every downstream state should see resampled examples; wrap only the final estimator if upstream preprocessing should learn from the original stream.

## Probability distributions

`proba` objects are streaming probability distributions. They expose `update`, `revert`, `sample`, `mode`, `n_samples`, and distribution-specific calls such as `cdf`.

- `proba.Beta`: binary-event probability distribution; useful for Bernoulli rewards and Thompson-style bandits.
- `proba.Gaussian`: univariate normal with streaming mean and variance.
- `proba.MultivariateGaussian`: multivariate normal over feature dictionaries, with covariance state.
- `proba.Multinomial`: categorical distribution over hashable events.

Useful patterns:

- Use distributions as bandit `reward_obj` values when a policy expects uncertainty-aware reward state.
- Wrap distributions with `utils.Rolling` or `utils.TimeRolling` when the distribution should only summarize recent observations.
- Use `revert` only when the distribution supports removal of the same type of observation that was previously added.
- Treat density values from `__call__` as scores, not normalized labels.
