# Decomposition workflows

Use these recipes after fitting a PCA-like estimator.

## Plot explained variance

```python
import matplotlib.pyplot as plt
import scikitplot as skplt
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA

X, y = load_iris(return_X_y=True)
pca = PCA().fit(X)

fig, ax = plt.subplots(figsize=(6, 4))
skplt.decomposition.plot_pca_component_variance(
    pca,
    target_explained_variance=0.75,
    ax=ax,
)
```

Use this when a user asks how many principal components explain a target fraction of variance. The highlighted marker reports the first component count that reaches the target when the target is attainable.

## Plot a 2-D projection

```python
import matplotlib.pyplot as plt
import scikitplot as skplt
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA

iris = load_iris()
pca = PCA(n_components=2, random_state=0).fit(iris.data)

fig, ax = plt.subplots(figsize=(6, 5))
skplt.decomposition.plot_pca_2d_projection(
    pca,
    iris.data,
    iris.target,
    ax=ax,
    cmap='Spectral',
)
```

Use `n_components=2` or greater. If the estimator transforms to only one component, the projection path cannot index the second component.

## Add a biplot

```python
skplt.decomposition.plot_pca_2d_projection(
    pca,
    iris.data,
    iris.target,
    biplot=True,
    feature_labels=iris.feature_names,
)
```

Biplots are best when the number of features is small enough for arrows and labels to remain readable. For high-dimensional data, plot the projection without biplot vectors or preselect important features.

## Axes reuse

All functions accept `ax=`. Keep the returned axes object when chaining or saving:

```python
out_ax = skplt.decomposition.plot_pca_component_variance(pca, ax=ax)
assert out_ax is ax
out_ax.figure.savefig('pca-variance.png')
```

## Smoke validation

```bash
python scripts/decomposition_smoke.py
```

The helper fits PCA on the Iris dataset, checks both decomposition plots, and closes all figures.
