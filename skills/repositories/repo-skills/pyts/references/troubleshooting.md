# Cross-Cutting Troubleshooting

## Purpose

Read this first when a pyts install, import, or smoke check fails before you
have narrowed the issue to one sub-skill.

## 1. `dtw` / classifier compatibility error

**Symptoms**
- `dtw` raises `TypeError: check_array() got an unexpected keyword argument 'force_all_finite'`.
- `python scripts/pyts_smoke.py --mode metrics` fails after a dependency
  upgrade.

**Likely cause**
- The installed scikit-learn is too new for this pyts snapshot.

**Recovery**
1. Pin a compatible scikit-learn version, such as `scikit-learn<1.6`.
2. Re-run `python -m pip check`.
3. Re-run `python scripts/pyts_smoke.py --mode metrics`.

## 2. Wrong environment or wrong import target

**Symptoms**
- `import pyts` succeeds in one shell but not another.
- The smoke script imports a different package than expected.

**Likely cause**
- The wrong Python interpreter is active, or the editable install was made into
  a different environment.

**Recovery**
1. Re-run the smoke helper with the environment's Python executable.
2. Confirm `import pyts; print(pyts.__version__)` reports `0.13.0` in the same
   interpreter that will run the downstream workflow.

## 3. Network-backed dataset fetches

**Symptoms**
- `fetch_ucr_dataset` or `fetch_uea_dataset` times out or fails.

**Likely cause**
- The dataset is remote, the cache is cold, or network access is blocked.

**Recovery**
1. Prefer the bundled loaders and the synthetic generator for smoke checks.
2. Check the dataset catalog helpers before retrying a remote fetch.
3. Treat remote fetches as an environment assumption rather than a guaranteed
   local capability.

## 4. First-run compile or runtime cost

**Symptoms**
- The first call to `dtw`, `boss`, or a feature transformer takes longer than
  later calls.

**Likely cause**
- Numba or other optimization code is compiling or warming up.

**Recovery**
- Re-run the same tiny smoke case once more before diagnosing a true hang.
- Keep the check small; do not jump straight to a benchmark-scale input.

## 5. Shape mismatch

**Symptoms**
- A transform or classifier rejects the input array shape.

**Likely cause**
- The data is really 2D when the workflow expects 3D, or vice versa.

**Recovery**
- Route to the relevant sub-skill and check its workflow reference for the
  expected shape.
