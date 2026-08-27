# mlxtend Cross-cutting Troubleshooting

Use this root troubleshooting reference for install/import, dependency, and cross-workflow issues. Workflow-specific failures live in the nearest sub-skill `references/troubleshooting.md`.

## Import or version failures

**Symptoms**
- `ModuleNotFoundError: No module named 'mlxtend'`.
- Import succeeds but expected classes/functions are missing.
- A future checkout behaves differently from this skill.

**Recovery**
1. Install the package in the active environment: `python -m pip install mlxtend`.
2. Check the version:
   ```bash
   python - <<'PY'
   import mlxtend
   print(mlxtend.__version__)
   PY
   ```
3. Run `python scripts/check_mlxtend_env.py` from this skill directory.
4. If a checkout/package version differs from `repo-provenance.md`, run `refresh-repo-skill` before relying on version-specific behavior.

## Dependency resolution issues

mlxtend depends on the scientific Python stack: NumPy, SciPy, pandas, scikit-learn, Matplotlib, and joblib. The metadata for this snapshot requires Python 3.11+.

**Symptoms**
- pip cannot find compatible wheels.
- sklearn/pandas/NumPy import errors after installation.
- `pip check` reports broken requirements.

**Recovery**
1. Prefer Python 3.11 or a newer version supported by all required wheels.
2. Use a clean virtual environment or conda environment rather than mixing old scientific packages.
3. Run `python -m pip check` after install.
4. Reinstall mlxtend after upgrading core dependencies; do not mix incompatible NumPy/scikit-learn builds from multiple package managers unless you know the ABI constraints.

## No CLI entry point

mlxtend is primarily a Python API package. If a user asks for an mlxtend CLI command, route them to Python snippets or the bundled scripts in this generated skill.

Useful checks:

```bash
python scripts/check_mlxtend_env.py --run-subskill-smokes
```

## Headless Matplotlib

Plotting helpers require Matplotlib. In server/CI/headless jobs:

```bash
MPLBACKEND=Agg python your_script.py
```

or call `matplotlib.use("Agg")` before importing `matplotlib.pyplot`. See `sub-skills/plotting-and-utilities/references/troubleshooting.md` for figure/axes and decision-region failures.

## sklearn estimator compatibility

Many mlxtend estimators and helpers expect sklearn-style APIs.

Common checks:

- Does the object implement `fit` and `predict`?
- Does the workflow require `predict_proba`?
- Is the estimator cloneable by sklearn (constructor parameters stored without mutation)?
- Are grid-search parameter names correctly prefixed, such as `meta_classifier__C` or estimator-specific names documented by `get_params()`?

Use `sub-skills/estimators-and-ensembles/references/troubleshooting.md` for ensemble/stacking details and `sub-skills/evaluation-and-validation/references/troubleshooting.md` for scoring/test mismatch details.

## pandas/NumPy shape issues

mlxtend APIs usually expect one of these schemas:

- `X`: 2D numeric array/dataframe with shape `(n_samples, n_features)`.
- `y`: 1D labels/targets with length `n_samples`.
- transaction data: list-of-lists before `TransactionEncoder`, or a one-hot boolean/0-1 pandas DataFrame for frequent-pattern algorithms.
- plotting matrices: 2D numeric arrays with labels that match dimensions.

Route shape-specific recovery:

- Feature selectors/preprocessing: `sub-skills/feature-workflows/references/data-formats.md`.
- Frequent patterns: `sub-skills/frequent-patterns/references/data-formats.md`.
- Plotting/data utilities: `sub-skills/plotting-and-utilities/references/data-formats.md`.

## Slow workflows

Some APIs intentionally refit models many times: exhaustive feature selection, sequential feature selection with cross-validation, bootstrap/permutation procedures, paired model-comparison tests, learning curves, and exhaustive grid searches.

Mitigation:

1. Start with tiny data, few folds/rounds, and deterministic seeds.
2. Use `n_jobs` only when supported and appropriate for the environment.
3. Prefer `StackingCV*` or statistical tests only when leakage control or statistical comparison is actually required.
4. Record approximations when reducing rounds/folds for a smoke test.

## Known file-group helper edge

In the inspected 0.25.0 snapshot, `find_filegroups` can raise `TypeError: 'module' object is not callable` because an internal helper is bound as a module in some import states. Use the compatibility recipe in `sub-skills/plotting-and-utilities/references/troubleshooting.md` or group files with `find_files` until the package is refreshed.
