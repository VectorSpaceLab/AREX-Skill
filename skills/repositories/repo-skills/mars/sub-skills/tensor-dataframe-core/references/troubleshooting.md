# Tensor and DataFrame Troubleshooting

## Common failures

### Importing `mars.dataframe` fails before you do anything

**Symptoms**
- `ImportError`, `AttributeError`, or a message mentioning `ray.__version__`.

**Likely causes**
- A shadowed `ray` directory/module is visible on the current path.
- A partial or broken optional `ray` install is present.

**Recovery**
- Run from a neutral directory with `python -I`.
- Remove the shadowing path or fix the optional Ray install.
- If the user does not need Ray, keep the CPU workflow but still repair the
  import environment before proceeding.

### `execute()` returns a Mars object instead of a concrete value

**Symptoms**
- The snippet prints a Mars object representation after `execute()`.

**Likely cause**
- Mars intentionally returns the same object so the caller can chain more work.

**Recovery**
- Call `.fetch()` after `execute()` if you want the NumPy or pandas value.

### Data looks lazy or does not compute immediately

**Symptoms**
- A tensor or DataFrame prints as a Mars object, not as the expected concrete
  result.

**Likely cause**
- Lazy execution is the default mode.

**Recovery**
- Use `.execute()` before `.fetch()`.
- For debugging, temporarily set `option_context({'eager_mode': True})`.

### `pip install -e` fails during setup

**Symptoms**
- Packaging errors about missing editable-install support.

**Likely cause**
- The current build backend stack does not support a PEP 660 editable install.

**Recovery**
- Use `pip install pymars` or another non-editable install instead.
- Set `NO_WEB_UI=1` if the optional web UI toolchain is not available.

### `pip check` reports scientific-stack conflicts

**Symptoms**
- Numpy, pandas, SciPy, or scikit-learn version conflicts after install.

**Likely causes**
- A too-new scientific stack is already present in the environment.
- A reused environment was mutated in place.

**Recovery**
- Align the environment with the package metadata.
- Prefer a private prefix over mutating an existing shared environment.

### Local IO examples fail on missing optional format packages

**Symptoms**
- HDF5, Zarr, Parquet, or SQL snippets fail with missing-package errors.

**Likely causes**
- The optional storage dependency was not installed.

**Recovery**
- Install only the specific extra that the format needs.
- For the base skill, keep the example tiny and local.

## Verification tip

If a tiny smoke fails, decide whether the failure is an API issue or an
environment issue before changing the workflow. The root install helper and the
sub-skill smoke helper are the fastest next checks.
