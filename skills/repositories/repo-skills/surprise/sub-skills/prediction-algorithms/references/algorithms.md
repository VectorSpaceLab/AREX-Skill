# Prediction algorithms reference

This reference keeps the algorithm catalog and parameter details out of the router file.

## Family guide

| Family | Classes | Best for | Key knobs |
| --- | --- | --- | --- |
| Random baseline | `NormalPredictor` | a quick sanity check and lower-bound baseline | no algorithm-specific constructor knobs |
| Bias-only | `BaselineOnly` | global mean plus user/item biases | `bsl_options` |
| Neighborhood | `KNNBasic`, `KNNWithMeans`, `KNNWithZScore`, `KNNBaseline` | similarity-driven prediction and neighbor inspection | `sim_options`, plus `bsl_options` for `KNNBaseline` and Pearson-baseline similarity |
| Factorization | `SVD`, `SVDpp`, `NMF` | latent-factor prediction | `random_state`, factor and regularization knobs; `SVDpp.cache_ratings`; `NMF.init_low` / `init_high` |
| Deviation / clustering | `SlopeOne`, `CoClustering` | simpler non-neighbor models | `random_state` for `CoClustering` |

## Prediction lifecycle

All built-ins inherit from `AlgoBase`.

1. Call `fit(trainset)` first. The base implementation stores `self.trainset` and resets cached baselines.
2. Call `predict(uid, iid, r_ui=None, clip=True, verbose=False)` with **raw** ids.
3. `predict()` converts raw ids to inner ids, calls `estimate(inner_u, inner_i)`, and wraps the result in a `Prediction(uid, iid, r_ui, est, details)` named tuple.
4. If `estimate()` returns `(est, details)`, the details dict is preserved.
5. If `estimate()` raises `PredictionImpossible`, `predict()` calls `default_prediction()` and sets `details['was_impossible'] = True` and `details['reason']`.
6. `test(testset)` simply loops over `(uid, iid, r_ui)` triples and returns a list of `Prediction` objects.

### `Prediction` fields

- `uid`: raw user id.
- `iid`: raw item id.
- `r_ui`: the true rating passed to `predict()` or `test()`.
- `est`: the estimated rating.
- `details`: algorithm-specific metadata, plus fallback flags when needed.

`clip=True` keeps estimates inside the dataset rating scale.

## Built-in algorithms

### `NormalPredictor`

- Predicts from a normal distribution fit on the training ratings.
- Good as a stochastic baseline.
- It uses NumPy's global RNG; seed NumPy if you need reproducible smoke output.

### `BaselineOnly`

- Predicts `μ + b_u + b_i`.
- Unknown users or items simply contribute a zero bias.
- `fit()` computes baselines immediately.

### `KNNBasic`

- Pure similarity-weighted average of neighbor ratings.
- Requires both user and item to be known; otherwise it raises `PredictionImpossible`.
- The `details` dict includes `actual_k` for the number of positive neighbors that were actually aggregated.
- If `actual_k < min_k`, the prediction becomes impossible and falls back to `default_prediction()`.

### `KNNWithMeans`

- Similar to `KNNBasic`, but subtracts neighbor means before aggregation.
- If not enough neighbors remain, the result falls back to the local mean `μ_u` or `μ_i` rather than raising.

### `KNNWithZScore`

- Similar to `KNNWithMeans`, but normalizes by user/item standard deviation.
- If a standard deviation is zero, the overall sigma is used instead.

### `KNNBaseline`

- Combines a baseline estimate with similarity-weighted residuals.
- This is the main class where `bsl_options` and `sim_options` interact.
- If user or item is unknown, it returns the baseline estimate without neighborhood correction.
- When `sim_options['name'] == 'pearson_baseline'`, baselines are computed first and then reused for similarity.

### `SVD`

- Factorization with optional biases.
- `biased=True` predicts `μ + b_u + b_i + q_i^T p_u` and can still use any available bias terms when only one side is known.
- `biased=False` removes the bias terms and requires both ids to be known.
- `random_state` controls factor initialization.

### `SVDpp`

- Extends `SVD` with implicit feedback terms.
- Supports `cache_ratings`; `True` uses more memory but speeds up training.
- Like biased `SVD`, it can still use known bias terms when only one side is known.
- `random_state` controls factor initialization.

### `NMF`

- Non-negative matrix factorization with positive latent factors.
- `init_low` must be non-negative.
- `biased=True` adds the same baseline machinery used by `SVD`.
- `biased=False` requires both ids to be known before it can estimate.
- `random_state` controls factor initialization.

### `SlopeOne`

- Uses average rating deviations between item pairs.
- Requires both ids to be known.
- Does not use similarity or baseline options.

### `CoClustering`

- Learns user clusters, item clusters, and co-clusters.
- Uses `random_state` for initialization.
- Missing-id behavior is model-specific; verify the current implementation before depending on a particular fallback.
- Does not use similarity options.

## Baseline options (`bsl_options`)

`bsl_options['method']` accepts:

- `als` (default)
- `sgd`

### ALS keys

- `n_epochs`: default `10`
- `reg_u`: default `15`
- `reg_i`: default `10`

### SGD keys

- `n_epochs`: default `20`
- `reg`: default `0.02`
- `learning_rate`: default `0.005`

Notes:

- `BaselineOnly` uses these options directly.
- `KNNBaseline` uses the same options for baseline centering.
- `pearson_baseline` similarity also consumes the computed baselines.

## Similarity options (`sim_options`)

`sim_options['name']` accepts:

- `cosine`
- `msd`
- `pearson`
- `pearson_baseline`

Other keys:

- `user_based`: default `True`. `False` switches the similarity domain to items.
- `min_support`: default `1`. Pairs below the support threshold get similarity `0`.
- `shrinkage`: default `100`. Only used by `pearson_baseline`.

`get_neighbors(inner_id, k)` returns inner ids from the same domain selected by `user_based`.

## Custom `AlgoBase` pattern

```python
from surprise import AlgoBase, PredictionImpossible

class MyAlgo(AlgoBase):
    def __init__(self, sim_options=None, bsl_options=None):
        super().__init__(sim_options=sim_options or {}, bsl_options=bsl_options or {})

    def fit(self, trainset):
        super().fit(trainset)
        # precompute what you need here
        return self

    def estimate(self, u, i):
        if not (self.trainset.knows_user(u) and self.trainset.knows_item(i)):
            raise PredictionImpossible("need known ids")
        est = self.trainset.global_mean
        details = {"source": "custom"}
        return est, details
```

Guidelines:

- Keep heavy work in `fit()`, not `estimate()`.
- Return `(est, details)` when you want metadata to flow into `Prediction.details`.
- Raise `PredictionImpossible` when you want `predict()` to invoke the fallback path.
- Use `compute_baselines()` and `compute_similarities()` only when the algorithm needs them.

## Choosing an algorithm quickly

- Use `BaselineOnly` when you want the cheapest strong baseline.
- Use `KNNBaseline` when you want a neighborhood model with baseline correction.
- Use `SVD` when you want the default latent-factor baseline.
- Use `SVDpp` when implicit feedback matters and extra memory is acceptable.
- Use `NMF` when non-negative factors are desirable.
- Use `SlopeOne` or `CoClustering` when the model family itself is the point of the experiment.
