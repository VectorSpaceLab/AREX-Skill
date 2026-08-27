# Workflows

## Matrix-profile check

1. Build a tiny univariate series.
2. Run `MatrixProfile(subsequence_length=..., implementation="numpy")` as the correctness baseline.
3. If `stumpy` is installed, run the same series with `implementation="stump"` and compare the outputs with `allclose`.
4. Treat `gpu_stump` as optional acceleration only; do not use it as the reference path.
5. Keep the input univariate. The current implementation does not support the multivariate case.

Recommended command:

- `python scripts/analysis_smoke.py matrix-profile`

## Serialization check

1. Fit a tiny estimator that inherits `BaseModelPackage`.
2. Confirm unfitted `to_json` and `to_pickle` raise `NotFittedError` before training.
3. Confirm unfitted `to_hdf5` raises `NotFittedError` when `h5py` is available.
4. Save to JSON and Pickle unconditionally.
5. Save to HDF5 only when `h5py` is installed.
6. Reload with `from_*` and compare predictions or transforms plus key fitted attributes.

The bundled smoke uses `KShape` as a compact fitted example because the persistence API is shared across tslearn estimators.

Recommended command:

- `python scripts/analysis_smoke.py serialization`

## Combined helper

- `python scripts/analysis_smoke.py all`

Use the combined run when you want one quick pass over both the matrix-profile backend choice and the persistence round-trip.
