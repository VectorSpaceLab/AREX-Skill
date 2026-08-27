# Unsupervised and reduction workflows

## Purpose

Use these recipes to cluster, embed, or compress MLAlgorithms data without reading the original repository's example files. The examples assume `mla`, NumPy, SciPy, and scikit-learn are installed.

## Choosing an unsupervised workflow

| Task shape | Good first choice | Use when | Watch for |
| --- | --- | --- | --- |
| Hard cluster labels | `KMeans` | you need fast, deterministic assignments | initialization choice and cluster count |
| Soft cluster membership | `GaussianMixture` | clusters overlap or ellipsoidal covariance matters | singular covariance and convergence |
| Low-dimensional features for a downstream model | `PCA` | you want linear compression with an interpretable basis | fit on training data only |
| 2D visualization | `TSNE` | you need a non-linear embedding for inspection | runtime cost and perplexity choice |
| Binary latent features | `RBM` | you want a simple unsupervised representation learner | reconstruction error, data scaling, and short smoke size |

## KMeans recipe

```python
from sklearn.datasets import make_blobs
from mla.kmeans import KMeans

X, y = make_blobs(n_samples=180, centers=4, n_features=2, random_state=42)
model = KMeans(K=4, max_iters=40, init="++")
model.fit(X)
labels = model.predict()
print(labels.shape, model.centroids)
```

If you want stable initialization, use `init="++"` rather than plain random selection.

## Gaussian mixture recipe

```python
from sklearn.datasets import make_blobs
from mla.gaussian_mixture import GaussianMixture

X, _ = make_blobs(n_samples=180, centers=3, n_features=2, random_state=42)
model = GaussianMixture(K=3, init="kmeans", max_iters=40)
model.fit(X)
assignments = model.predict(X)
print(assignments.shape, len(model.likelihood))
```

If `covs` become singular or a cluster gets almost no points, reduce `K`, add samples, or switch to KMeans first to inspect the geometry.

## PCA recipe

```python
from sklearn.datasets import make_classification
from mla.pca import PCA

X, y = make_classification(n_samples=220, n_features=20, n_informative=10, random_state=1111)
X_train, X_test = X[:160], X[160:]
model = PCA(5, solver="svd")
model.fit(X_train)
X_train_5 = model.transform(X_train)
X_test_5 = model.transform(X_test)
print(X_train_5.shape, X_test_5.shape)
```

Treat `fit` on the training split only as part of the workflow, then transform every downstream split with the same mean/components.

## t-SNE recipe

```python
from sklearn.datasets import make_classification
from mla.tsne import TSNE

X, _ = make_classification(n_samples=80, n_features=12, n_informative=6, random_state=1111)
embedding = TSNE(n_components=2, perplexity=10.0, max_iter=150, learning_rate=200).fit_transform(X)
print(embedding.shape)
```

Keep `n_samples` small. The implementation computes dense pairwise distances and many Python-level loops, so this is a visualization helper rather than a general-purpose large-data embedding tool.

## RBM recipe

```python
import numpy as np
from mla.rbm import RBM

X = np.random.RandomState(0).uniform(0, 1, (60, 8))
rbm = RBM(n_hidden=4, learning_rate=0.05, batch_size=10, max_epochs=3)
rbm.fit(X)
features = rbm.predict(X)
print(features.shape, len(rbm.errors))
```

Use a small number of epochs for smoke checks. The model is educational and the reconstruction error is a useful progress signal.

## Demo dataset loaders

- `load_mnist()` returns arrays already reshaped for the ConvNet recipe in the neural sub-skill.
- `load_nietzsche()` returns one-hot character sequences for recurrent examples in the neural sub-skill.
- When using modern NumPy, prefer an environment pinned below `1.24` or a patched checkout because the current source references `np.bool` in `load_nietzsche()`.

## Safe bundled smoke

Run the helper when you need a small no-display check. From this sub-skill directory, use:

```bash
python scripts/run_unsupervised_smoke.py --workflow all
```

From the root `ml-algorithms` skill directory, use `python sub-skills/unsupervised-and-reduction/scripts/run_unsupervised_smoke.py --workflow all`.

The helper uses synthetic data and prints assignments, shapes, and error counts instead of opening plots.
