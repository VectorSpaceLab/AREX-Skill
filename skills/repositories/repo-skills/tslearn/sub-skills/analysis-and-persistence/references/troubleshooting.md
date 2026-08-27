# Troubleshooting

## Missing `stumpy`

**Symptoms**
- `MatrixProfile(..., implementation="stump")` raises `ImportError`
- `MatrixProfile(..., implementation="gpu_stump")` raises `ImportError`

**Fix**
- Use `implementation="numpy"` for the baseline
- Install `stumpy` to enable the CPU-backed `stump` path

## Missing `h5py`

**Symptoms**
- `to_hdf5` or `from_hdf5` raises `ImportError`

**Fix**
- Use JSON and Pickle round-trips instead
- Install `h5py` only when you need the HDF5 path

## Unfitted estimator serialization

**Symptoms**
- `to_json`, `to_pickle`, or `to_hdf5` raises `NotFittedError`

**Fix**
- Fit the estimator first
- The smoke script checks the unfitted failure before it writes any files

## Optional GPU-stump confusion

**Symptoms**
- `gpu_stump` fails on a machine without a compatible GPU, even if `stumpy` is installed

**Fix**
- Treat `gpu_stump` as optional acceleration only
- Use `stump` for CPU verification and keep `numpy` as the correctness baseline

## Matrix-profile shape mismatch

**Symptoms**
- `MatrixProfile.transform` fails on multivariate input

**Fix**
- Keep the bundled checks univariate
- Route preprocessing or reshaping concerns to the data-preparation sub-skill
