# Unsupervised Workflows

Use these recipes as self-contained operating guidance for ML-From-Scratch
unsupervised workflows. For install/import context see
`../../../references/package-overview.md` and for shared preprocessing helpers
see `../../../references/shared-utilities.md`.

## 1. Clustering smoke and model selection

Start with the bundled smoke check when validating an environment or a minimal
cluster workflow:

```bash
python scripts/run_clustering_smoke.py
```

Minimal in-memory pattern:

```python
import numpy as np
from mlfromscratch.unsupervised_learning import KMeans, DBSCAN, PAM, GaussianMixtureModel, PCA
from mlfromscratch.utils import standardize

np.random.seed(7)
X = np.asarray(X, dtype=float)
X_scaled = standardize(X.copy())  # or use a domain-specific scaler

labels = KMeans(k=3, max_iterations=100).predict(X_scaled)
projection = PCA().transform(X_scaled, 2)
```

Choose the algorithm by data shape and failure mode:

- `KMeans`: compact, roughly spherical clusters; fastest default; requires `k`.
- `PAM`: medoid-based alternative when means are not representative or outliers
  matter; requires `k`; slower than KMeans.
- `DBSCAN`: density-separated clusters and noise detection; no `k`; tune `eps`
  and `min_samples` after scaling.
- `GaussianMixtureModel`: probabilistic soft-density model with full covariance;
  useful when ellipsoidal components are plausible and enough samples exist.
- `PCA`: dimensionality reduction or visualization before/after clustering; it
  is not a clustering model.

Expected observations:

- Every `predict(X)` call returns exactly one label per row of `X`.
- Label numbers are arbitrary and may change across seeds.
- PCA returns a dense numeric projection with the requested number of columns.
- For visualization in headless sessions, set `MPLBACKEND=Agg` before importing
  plotting libraries and save figures instead of calling interactive display.

## 2. DBSCAN parameter diagnosis loop

When DBSCAN returns one label for everything or mostly its default outlier label:

1. Ensure all features are numeric and scaled; `eps` is measured in the resulting
   feature units.
2. Print distances to a few nearest neighbors or sweep a small list of `eps`
   values around the expected within-cluster distance.
3. Lower `min_samples` for tiny synthetic data; increase it for noisy larger
   datasets.
4. Count labels instead of assuming noise is `-1`; this implementation uses a
   nonnegative default label for samples not assigned to a discovered cluster.
5. If the result is still unstable, try PCA to 2-D for inspection and compare
   with KMeans/PAM as a sanity check.

## 3. Association mining with string transactions

Use the bundled association smoke to verify both Apriori and FPGrowth:

```bash
python scripts/run_association_smoke.py
```

Apriori expects singleton items to behave like integers in its candidate logic.
For user-provided string transactions, map items to stable integer IDs before
calling Apriori, then decode the returned itemsets and rules.

```python
from mlfromscratch.unsupervised_learning import Apriori, FPGrowth

transactions = [
    ["milk", "bread", "eggs"],
    ["milk", "bread"],
    ["bread", "eggs"],
]

items = sorted({item for tx in transactions for item in tx})
item_to_id = {item: i + 1 for i, item in enumerate(items)}
id_to_item = {i: item for item, i in item_to_id.items()}
encoded = [[item_to_id[item] for item in sorted(tx)] for tx in transactions]

apriori = Apriori(min_sup=0.5, min_conf=0.6)
encoded_itemsets = apriori.find_frequent_itemsets(encoded)
rules = apriori.generate_rules(encoded)

fp = FPGrowth(min_sup=2)  # count, not fraction, in this implementation
fp_itemsets = fp.find_frequent_itemsets(transactions)
```

Interpretation:

- Apriori `support` is the fraction of all transactions containing the complete
  itemset.
- Apriori `confidence` is `support(antecedent ∪ consequent) / support(antecedent)`.
- Apriori rule objects expose `rule.antecedent`, `rule.concequent`,
  `rule.support`, and `rule.confidence`; keep the package's misspelled field
  name when reading rule objects.
- FPGrowth returns frequent itemsets only; it does not generate association
  rules in this package.

## 4. Genetic string search

Use a small target and bounded iterations for deterministic smoke checks:

```bash
python scripts/run_optimization_smoke.py --target AI --population-size 12 --iterations 5
```

Recipe:

```python
import numpy as np
from mlfromscratch.unsupervised_learning import GeneticAlgorithm

np.random.seed(3)
ga = GeneticAlgorithm(target_string="AI", population_size=12, mutation_rate=0.2)
ga.run(iterations=10)
```

Guidelines:

- Use only space and ASCII letters in `target_string`.
- Use an even `population_size` because reproduction creates children in pairs.
- Treat printed progress as the primary output; the class does not return the
  best candidate from `run`.
- Keep iterations low for usability checks; long runs are stochastic demos.

## 5. RBM reconstruction workflow

RBM is best treated as an advanced reconstruction workflow rather than a default
smoke test.

```python
import numpy as np
from mlfromscratch.unsupervised_learning import RBM

np.random.seed(11)
X = np.asarray(X, dtype=float)
X = np.clip(X, 0.0, 1.0)

rbm = RBM(n_hidden=8, learning_rate=0.01, batch_size=4, n_iterations=3)
rbm.fit(X)
reconstructed = rbm.reconstruct(X[:4])
errors = rbm.training_errors
```

Expected observations:

- `fit` prints a progress bar and fills `training_errors`.
- `training_reconstructions` stores reconstruction snapshots from sampled
  batches.
- Inputs should be binary or scaled into `[0, 1]` for Bernoulli visible units.
- Reconstruction demos can be much slower than clustering and association
  smokes; reduce `n_hidden`, `batch_size`, and `n_iterations` first.
