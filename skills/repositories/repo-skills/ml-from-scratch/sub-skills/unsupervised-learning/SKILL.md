---
name: unsupervised-learning
description: "Run and debug ML-From-Scratch unsupervised PCA, clustering,
  association mining, GMM, genetic search, and RBM workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ML-From-Scratch Unsupervised Learning

Use this sub-skill when a task asks for ML-From-Scratch workflows in clustering,
dimensionality reduction, density modeling, association mining, transaction
rules, string-target genetic search, or RBM reconstruction. It assumes the
`mlfromscratch` package is importable in a CPU Python environment and keeps all
runtime guidance self-contained.

## Route here

- PCA dimensionality reduction with `PCA().transform(X, n_components)`.
- Clustering with `KMeans`, `DBSCAN`, `PAM`, or `GaussianMixtureModel`.
- Frequent itemset and rule mining with `Apriori` or `FPGrowth`.
- Toy optimization/search with `GeneticAlgorithm` targeting a string.
- Advanced unsupervised reconstruction with `RBM`.

## Route elsewhere

- Supervised regressors, classifiers, trees, ensembles, Bayes, LDA, SVM,
  boosting, and supervised neural estimators: `../supervised-learning/`.
- Low-level neural-network layers, losses, optimizers, CNN/RNN/MLP, GAN,
  DCGAN, and autoencoder assembly details: `../deep-learning/`.
- CartPole, DQN, Gym reset/step compatibility, replay memory, and rendering:
  `../reinforcement-learning/`.
- Cross-cutting package install/import issues: `../../references/troubleshooting.md`.

## Start with these references

- `references/algorithm-catalog.md` for constructors, methods, return values,
  state, and known API quirks.
- `references/workflows.md` for safe recipes: clustering/PCA, association
  mining with string normalization, genetic search, and RBM reconstruction.
- `references/troubleshooting.md` for scaling, DBSCAN density parameters,
  KMeans empty clusters, transaction formatting, support/confidence, RBM speed,
  and headless plotting.
- `../../references/package-overview.md` for package-level install context.
- `../../references/shared-utilities.md` for shared helpers such as
  `normalize`, `standardize`, `euclidean_distance`, and plotting helpers.

## Fast bundled checks

Run these from this sub-skill directory or adapt their in-memory patterns:

```bash
python scripts/run_clustering_smoke.py --help
python scripts/run_clustering_smoke.py
python scripts/run_association_smoke.py
python scripts/run_optimization_smoke.py --iterations 5
```

The bundled scripts avoid network access, credentials, destructive writes, and
interactive plotting. They are smoke checks for import/API usability, not
benchmark or quality claims.

## Operating reminders

- These classes use repo-specific APIs, not scikit-learn estimators. Most
  clustering classes expose `predict(X)` directly; PCA exposes
  `transform(X, n_components)`; there is often no separate `fit` call.
- Cluster labels are arbitrary IDs. Compare partitions by counts, separation,
  or downstream use rather than expecting fixed label numbers.
- Set `numpy.random.seed(...)` before KMeans, PAM, GMM, or GeneticAlgorithm when
  a deterministic result is needed.
- Scale or standardize numeric features before distance- or covariance-based
  algorithms unless all features are already comparable.
- Normalize string transactions before Apriori; use count-style support for
  FPGrowth in this implementation.
- Treat RBM as an advanced, slower reconstruction workflow. Start with tiny
  batches and few iterations before scaling up.
