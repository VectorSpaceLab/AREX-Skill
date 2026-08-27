# Installation and Backend Troubleshooting

## Missing package or import

**Symptom:** `ModuleNotFoundError: phi` or `ModuleNotFoundError: phiml`.

**Likely cause:** the package was never installed into the environment you are
using, or a different Python is active.

**Recovery:**

1. Run `python -m pip install -e .` from the checkout, or install `phiflow`
   from PyPI.
2. Re-run `python scripts/check_install.py --show-backends`.
3. If the error persists, inspect the environment's `python` and `pip` rather
   than relying on shell activation assumptions.

## Minimal config failure

**Symptom:** `phi.verify()` prints an error about NumPy, SciPy, or the minimal
configuration.

**Likely cause:** the environment is incomplete or a dependency was removed.

**Recovery:** reinstall the package set in a fresh environment or repair the
broken dependency, then rerun the install smoke.

## Missing Dash / Plotly

**Symptom:** `phi.verify()` says Dash is not installed or Plotly is missing.

**Likely cause:** the optional web-UI dependencies were skipped.

**Recovery:** install `dash` and `plotly`. If you only need Matplotlib plots,
this warning is not blocking.

## Missing backend names

**Symptom:** `phi.detect_backends()` omits `torch`, `jax`, or `tensorflow`.

**Likely cause:** the backend wheel is not installed, or the wheel does not
match the host platform / Python version.

**Recovery:** install the correct backend build, then rerun the smoke check.
Do not claim backend support until the backend appears in the detected list.

## Stale environment vs current checkout

**Symptom:** the skill still works, but the checkout or installed version has
moved ahead.

**Likely cause:** the checkout commit or package version no longer matches the
stored provenance snapshot.

**Recovery:** read `../../references/repo-provenance.md` and refresh the skill if
needed.
