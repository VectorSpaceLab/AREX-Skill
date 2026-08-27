# Unsupervised and reduction troubleshooting

## Purpose

Use this reference when clustering, reduction, RBM, or dataset-loading workflows fail, produce singular matrices, or are too slow for a quick check.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mla'` | The package is not installed in the current environment. | Install the package and rerun the bundled smoke script. |
| `ImportError` from SciPy | SciPy is missing or incompatible. | Install the scientific stack that the repo requires. |
| `NameError` or `AttributeError` around `np.bool` | NumPy is too new for the current `load_nietzsche()` implementation. | Use NumPy `< 1.24` or patch the loader to `bool`/`np.bool_`. |

## Cluster and mixture failures

- `KMeans` returns odd assignments: check `K`, `init`, and whether `fit` was called before `predict`. The class predicts on the stored training data.
- `KMeans` or GMM output varies run to run: set random seeds before fitting and keep synthetic datasets small.
- `GaussianMixture` throws covariance or PDF errors: a cluster may be nearly empty or singular. Reduce `K`, provide more points, or initialize with `init="kmeans"` first.
- `GaussianMixture` likelihood stalls: the current implementation uses full covariance matrices, so tiny datasets can converge poorly. Reduce dimensionality first or simplify the cluster geometry.

## PCA and t-SNE failures

- `PCA` fit/test leakage: fit on the training split only, then transform held-out data.
- `PCA` output shape wrong: ensure `n_components <= n_features`.
- `TSNE` takes too long: reduce `n_samples`, lower `max_iter`, or use PCA first.
- `TSNE` embedding looks collapsed: perplexity may be too high for the sample count. A rough rule is to keep perplexity well below the number of samples.

## RBM failures

- `RBM` errors explode or do not improve: scale inputs to `[0, 1]`, lower `learning_rate`, reduce `batch_size`, or run fewer epochs.
- `RBM` smoke takes too long: decrease `max_epochs` and sample count. The model is not intended for large-scale training in this skill.
- `predict` shape unexpected: `RBM.predict(X)` returns hidden-unit probabilities with one row per sample.

## Plotting and display issues

- `plot()` or `plt.show()` blocks in CI/headless runs: do not call the plotting methods in automated workflows. Use the bundled smoke script or inspect arrays only.
- `GaussianMixture.plot()` requires 2D data: pass only 2D features if you need visual diagnostics.

## Data-loader caveats

| Loader | Caveat | Recovery |
| --- | --- | --- |
| `load_mnist()` | Reads packaged IDX files and returns image arrays shaped for ConvNet workflows. | Make sure package data was installed with the distribution. |
| `load_nietzsche()` | Uses deprecated `np.bool` in the current source version. | Pin NumPy below 1.24 or patch the source. |

## Safe next checks

1. Run `scripts/run_unsupervised_smoke.py --workflow kmeans`.
2. If the failure is in PCA or t-SNE, check the feature count and sample count before changing algorithm parameters.
3. If the failure is in the dataset loaders, verify the installed package includes the bundled data files and that NumPy is compatible.
