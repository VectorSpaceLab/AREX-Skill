# Specialized Workflows Troubleshooting

## Install and import failures

### `ModuleNotFoundError: No module named 'river'`

Check:

```python
import river
print(river.__version__)
```

Fixes:

- Install the `river` package in the active Python environment.
- If installing from source, ensure the Rust extension build completed and the active Python runtime can import River modules.
- Use the bundled smoke script to isolate whether the failure is global import, a specific module, or an optional dependency.

## Drift detector state interpretation

### `drift_detected` is missed or seems to disappear

Cause: the flag describes the most recent `update`. Some detectors reset or trim internal state after drift.

Fix:

```python
for i, value in enumerate(values):
    detector.update(value)
    if detector.drift_detected:
        drift_indices.append(i)
```

Record the event before the next update.

### `warning_detected` is missing

Cause: not every detector supports warnings. `PageHinkley`, `ADWIN`, and `KSWIN` expose drift state; binary DDM-family detectors expose warnings.

Fixes:

- Guard warning reads with `hasattr(detector, "warning_detected")`.
- For `DriftRetrainingClassifier(train_in_background=True)`, use a warning-capable detector such as `drift.binary.DDM`, `EDDM`, `HDDMA`, or `HDDMW`.
- If only drift state is available, set `train_in_background=False` or implement a custom manual retraining loop.

### Binary detector never fires

Likely causes:

- Feeding raw labels instead of error bits.
- Feeding `True` for correct predictions instead of incorrect predictions.
- Warm-up or thresholds are too conservative for the stream length.

Fix:

```python
error = int(y_pred != y)
detector.update(error)
```

## Anomaly score thresholding

### Anomaly scores are used as predicted labels

Cause: `score_one` returns a continuous score where higher means more anomalous. It is not a class label.

Fixes:

- Use score/ranking metrics, such as ROC AUC, when evaluating raw scores.
- Use `ThresholdFilter` or `QuantileFilter` before classification metrics.
- Store the threshold rule next to reported binary anomaly metrics.

### Filter update behavior is not what you expected

Causes:

- `protect_anomaly_detector=True` prevents anomalous samples from updating the wrapped detector.
- Disabled protection has filter-specific behavior; `QuantileFilter` explicitly updates when protection is disabled, while `ThresholdFilter` uses the shared filter learning path.
- The wrapped detector might also be updated manually elsewhere.

Fixes:

```python
filtered = anomaly.ThresholdFilter(detector, threshold=0.95, protect_anomaly_detector=True)
```

If anomalous samples should become part of a new normal regime, verify the exact filter behavior with a tiny stream or update the wrapped detector explicitly in a manual loop.

### `HalfSpaceTrees` returns low or zero scores

Likely causes:

- The detector is still in its warm-up window.
- Feature values are not in `[0, 1]` and no `limits` were supplied.
- Score-before-learn and learn-before-score were mixed across experiments.

Fixes:

- Warm up with at least the configured `window_size` before trusting scores.
- Scale features or pass explicit `limits`.
- Use the same scoring order consistently in evaluation.

## Clustering metric choices

### `Silhouette.update` fails or stays empty

Cause: internal clustering metrics need features, predicted cluster, and current centers.

Fix:

```python
y_pred = model.predict_one(x)
metric.update(x, y_pred, model.centers)
```

If there is only one current cluster or the predicted label is not present in `centers`, River's online `Silhouette` skips the update.

### External clustering metric gives confusing results

Cause: external metrics compare predicted clusters to known labels and are label-invariant, but they still require aligned `y_true`/`y_pred` pairs.

Fixes:

- Use `AdjustedRand`, `Rand`, `Homogeneity`, `Completeness`, or `VBeta` only when true labels exist.
- Do not pass feature dictionaries or centers to external multi-class metrics.
- Treat arbitrary cluster IDs as labels; do not expect them to match human-readable class names.

### Micro-cluster algorithms report more clusters than expected

Likely causes:

- You are inspecting micro-clusters rather than macro-clusters.
- Cleanup, fading, minimum weight, or reclustering parameters have not yet produced stable macro-clusters.

Fixes:

- Distinguish `micro_clusters`, `clusters`, and `centers` in reports.
- For density algorithms, confirm whether the task wants online micro-cluster state or final macro-cluster assignments.

## Forecasting horizon and metric mismatches

### `ValueError: the length of xs should be equal to the specified horizon`

Cause: `forecast(horizon, xs=...)` received the wrong number of future feature dictionaries.

Fix:

```python
future_xs = [features_for_t_plus_1, features_for_t_plus_2]
y_pred = model.forecast(horizon=2, xs=future_xs)
```

Use `xs=None` for univariate forecasting with no future exogenous features.

### Ordinary regression metric output is missing per-horizon detail

Cause: ordinary progressive validation evaluates one prediction per sample. Forecasting evaluation must compare a vector of horizon predictions.

Fix:

```python
metric = evaluate.evaluate(dataset, forecaster, metrics.MAE(), horizon=4)
print(metric.get())  # one value per horizon step
```

Pass `agg_func` only when a single aggregate across horizons is intended.

### Forecasts look shifted by one or more steps

Likely causes:

- The stream is not ordered by time.
- The dataset has gaps but the forecaster assumes uniformly spaced observations.
- Exogenous `xs` contain features from the wrong future step.

Fixes:

- Sort the stream by time before evaluation.
- Match `horizon` to the true number of future steps.
- Keep a clear convention for `t + 1`, `t + 2`, ..., `t + horizon` feature availability.

## Bandit reward and history format

### `evaluate_offline` uses very few samples

Cause: replay only updates when the policy selects the same arm as the logged arm.

Check:

```python
reward_stat, n_used = bandit.evaluate_offline(policy, history)
print(n_used)
```

Fixes:

- Expect `n_used` to be smaller than the log size.
- Ensure each history row is `(arms_available, context, logged_arm, reward)`.
- Include all arms that were available at decision time, not only the logged arm.

### Contextual policy update fails

Cause: contextual policies require context in both `pull` and `update`.

Fix:

```python
arm = policy.pull(arms, context=x)
policy.update(arm, x, reward)
```

For non-contextual policies, call `policy.pull(arms)` and `policy.update(arm, reward)`.

### Reward object rejects reward input

Cause: the chosen `reward_obj` expects a different update signature or value range.

Fixes:

- Use `stats.Mean()` or `stats.Sum()` for scalar rewards.
- Use `proba.Beta()` for boolean success/failure rewards.
- Use a reward scaler only with univariate reward objects that support direct scalar updates.

## Recommender user/item IDs

### `rank` returns unexpected items or ties

Likely causes:

- Candidate `items` set omitted items that should be ranked.
- New users/items have no learned state and default/bias terms dominate.
- The model ignores context even though context was supplied.

Fixes:

- Pass the complete candidate set to `rank(user, items, x=None)`.
- Warm-start frequent users/items or handle cold-start rankings separately.
- Check `model.is_contextual`; if it is `False`, supplied context will not change rankings.

### `learn_one` receives a feature dict and fails

Cause: `reco` rankers expect `user`, `item`, `y`, and optional context separately.

Fix:

```python
model.learn_one(user="alice", item="article-1", y=1.0, x={"time": "morning"})
```

For feature-dict CTR modeling, use `facto` classifiers instead.

## Factorization machine feature issues

### Field-aware model interactions look wrong

Cause: field-aware models infer field names from the substring before the first underscore.

Fixes:

- Use feature names such as `user_alice`, `item_article_1`, and `slot_top` when fields matter.
- For plain `FMClassifier` or `FMRegressor`, field names are not used.
- Use `debug_one(x)` to inspect interaction contributions.

### Categorical strings behave differently from numeric IDs

Cause: string feature values are one-hot encoded as categorical variables; numeric feature values are used as numeric magnitudes.

Fixes:

- Keep categorical IDs as strings when they represent categories.
- Scale numeric features before factorization models when feature magnitudes vary widely.

## Imbalanced sampler placement

### The sampler appears to ignore preprocessing

Cause: the sampler only controls what the wrapped estimator sees. Placement determines which components are before or inside the sampling boundary.

Fixes:

- If preprocessing should learn from every original sample, put preprocessing before the sampler and wrap only the final classifier.
- If preprocessing should see the resampled stream too, wrap the entire preprocessing-plus-classifier pipeline inside the sampler.
- Keep `desired_dist` keys identical to the labels in the stream and make values sum to `1` for random over/under samplers.

### Regression sampler changes results unexpectedly

Cause: Chebyshev and hard-sampling wrappers intentionally bias the stream toward rare or hard target values.

Fixes:

- Compare against the same regressor without the sampler.
- Report both ordinary regression metrics and behavior on rare target ranges.
- Keep buffer size and replay probability explicit for hard samplers.

## Probability distribution issues

### Distribution density is interpreted as a probability label

Cause: `dist(x)` returns a mass or density value, not a class label.

Fixes:

- Use `mode` for the most likely event/value.
- Use `cdf` for continuous cumulative probability when available.
- Use downstream thresholds only after validating the score distribution.

### Rolling distribution state seems to forget old samples

Cause: `utils.Rolling` and `utils.TimeRolling` intentionally call `revert` on observations leaving the window.

Fixes:

- Use the bare distribution for all-time state.
- Use rolling wrappers only when recent-window behavior is desired.

## Optional notebook and environment dependencies

### Bandit environment examples fail to import `gymnasium`

Cause: Gym-style environments are optional. Bandit policies and offline replay do not require them.

Fixes:

- Use direct `pull`/`update` loops or `bandit.evaluate_offline` for dependency-free checks.
- Install `gymnasium` only when live environment benchmarking is needed.

### Plotting, notebook, or dataframe examples fail

Cause: notebooks often use optional packages such as plotting libraries, progress bars, or dataframes.

Fixes:

- Keep runtime checks synthetic and console-only.
- Add optional packages only for the exact workflow that needs them.
- Prefer the bundled smoke script for quick validation; it avoids notebooks and external data.
