# Unsupervised Algorithm Catalog

This catalog summarizes the ML-From-Scratch unsupervised classes that are owned
by this sub-skill. See `workflows.md` for recipes and `troubleshooting.md` for
failure diagnosis.

## Import surface

```python
from mlfromscratch.unsupervised_learning import (
    PCA, KMeans, DBSCAN, PAM, GaussianMixtureModel,
    Apriori, FPGrowth, GeneticAlgorithm, RBM,
)
```

## Numeric workflows

| Algorithm | Constructor | Main call | Input and output | Notes |
|---|---|---|---|---|
| PCA | `PCA()` | `transform(X, n_components)` | `X` is a 2-D numeric array; returns an `(n_samples, n_components)` projection. | Component count is passed to `transform`, not the constructor. Use finite numeric data and prefer standardized features when units differ. |
| KMeans | `KMeans(k=2, max_iterations=500)` | `predict(X)` | Returns one cluster label per sample, usually as numeric IDs. | Random centroid initialization; set `numpy.random.seed` for reproducibility. Empty clusters can produce invalid centroids if `k` is too high or initialization duplicates a point. |
| DBSCAN | `DBSCAN(eps=1, min_samples=5)` | `predict(X)` | Returns one density-cluster label per sample. | `eps` is a distance radius in the scaled feature space. Outliers/noise are assigned the default nonnegative label equal to the number of discovered clusters, not scikit-learn's `-1`. |
| PAM | `PAM(k=2)` | `predict(X)` | Returns medoid-cluster labels. | Random medoid initialization. More robust to outliers than KMeans, but slower because it tests medoid swaps. |
| GaussianMixtureModel | `GaussianMixtureModel(k=2, max_iterations=2000, tolerance=1e-8)` | `predict(X)` | Returns the component with highest posterior responsibility for each sample. | Uses random Gaussian initialization and full covariance estimates. Needs enough non-degenerate samples per component; singular covariance can destabilize likelihoods. |

## Transaction mining workflows

| Algorithm | Constructor | Main calls | Input and output | Notes |
|---|---|---|---|---|
| Apriori | `Apriori(min_sup=0.3, min_conf=0.81)` | `find_frequent_itemsets(transactions)`, `generate_rules(transactions)` | `transactions` is a list of transactions; frequent itemsets are integers or lists; rules expose `antecedent`, `concequent`, `support`, and `confidence`. | `min_sup` is a fraction of transactions. Internally, singleton itemsets are treated as integers, so string items should be mapped to stable integer IDs before mining and decoded afterward. The rule field is intentionally spelled `concequent` in the package API. |
| FPGrowth | `FPGrowth(min_sup=0.3)` | `find_frequent_itemsets(transactions, suffix=None, show_tree=False)` | Returns frequent itemsets as lists. `show_tree=True` prints the tree. | This implementation compares raw support counts to `min_sup`; use integer counts such as `3`, not fractions, for predictable behavior. Prefer a fresh instance per mining run because results are kept on the object. |

## Optimization and reconstruction workflows

| Algorithm | Constructor | Main calls | Input and output | Notes |
|---|---|---|---|---|
| GeneticAlgorithm | `GeneticAlgorithm(target_string, population_size, mutation_rate)` | `run(iterations)` | Evolves strings toward `target_string` and prints progress; no structured return value. | Target characters must come from space plus ASCII letters. Use an even population size and seed NumPy for deterministic smoke checks. Keep iterations bounded. |
| RBM | `RBM(n_hidden=128, learning_rate=0.1, batch_size=10, n_iterations=100)` | `fit(X, y=None)`, `reconstruct(X)` | `X` is a 2-D visible-unit matrix, usually binary or scaled to `[0, 1]`; `reconstruct` returns visible probabilities. | Uses progressbar output and stores `training_errors` plus `training_reconstructions`. It is slower than the classical algorithms; start tiny. |

## Cross-links

- Use `workflows.md` for end-to-end recipes and safe script entry points.
- Use `troubleshooting.md` when labels collapse, itemsets are empty, or plotting
  and RBM runs are too slow.
- Use `../../../references/shared-utilities.md` for shared normalization,
  standardization, distance, batching, and plotting helper behavior.
