# Troubleshooting

## Import fails on modern Python

If `import numpy_ml` fails with `cannot import name 'Hashable' from 'collections'`,
use Python 3.8 for this legacy snapshot or apply a reviewed compatibility patch
that imports `Hashable` from `collections.abc`.

## NumPy alias errors

If a path fails with errors involving `np.int` or `np.float`, use `numpy<1.24`
for the unpatched snapshot. Do not treat a root import as full proof that every
model path works under NumPy 1.24+.

## Missing optional dependencies

- Missing `gym`: only a block for real RL environment training.
- Missing `matplotlib`/`seaborn`: only a block for plotting.
- Missing scikit-learn, torch, TensorFlow, NLTK, huffman, librosa, networkx, or
  statsmodels: usually only a block for original comparison tests.

Start with the bundled smoke scripts before installing broad optional groups.

## `fit` return confusion

Many APIs mutate the object and return `None`. Keep the object and then call
`predict`, inspect parameters, or check learned attributes.

## Safe verification order

1. Run `scripts/check_numpy_ml_environment.py`.
2. Run `scripts/api_smoke_matrix.py` for cross-family coverage.
3. If a sub-skill-specific task fails, run that sub-skill's smoke helper.
4. Only run original native tests after installing their optional dependencies
   in a separate, user-approved test environment.

## When not to use this skill

Use another framework-specific skill when the task needs production estimators,
a scikit-learn estimator interface, PyTorch/TensorFlow/JAX training, modern RL
experiment operations, GPU acceleration, or model serving.
