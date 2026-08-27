# Compatibility

## Verified runtime baseline

This skill was created against `numpy-ml` 0.1.2 at the recorded repository
snapshot. The verified inspection environment used:

- Python 3.8;
- `numpy==1.23.5`;
- `scipy==1.10.1`;
- editable local package install for inspection.

For normal users, install the package and keep the same constraints when using
this legacy snapshot:

```bash
python -m pip install "numpy<1.24" "scipy<1.11" numpy-ml
python - <<'PY'
import numpy_ml
print('numpy-ml import ok')
PY
```

## Known legacy limits

- Python 3.10+ fails at this commit because the package imports
  `collections.Hashable`.
- NumPy 1.24+ can fail on code paths using removed aliases such as `np.int` or
  `np.float`.
- The package is written for clarity and educational experiments, not for
  production throughput or modern accelerator backends.

## Optional dependency groups

| Surface | Optional dependencies | Notes |
| --- | --- | --- |
| RL training | `gym` from the `rl` extra; pandas may be useful for environment stats | Required only for real environment training. |
| Plotting demos | matplotlib, seaborn, sometimes scikit-learn, gym, hmmlearn | Keep plotting disabled for smoke checks. |
| Original comparison tests | scikit-learn, torch, tensorflow, nltk, huffman, librosa, networkx, statsmodels, pytest | Broad and not installed by the minimum runtime plan. |

Do not install `requirements-dev.txt` or `requirements-test.txt` just to use the
runtime APIs unless the user explicitly asks to run original native tests.
