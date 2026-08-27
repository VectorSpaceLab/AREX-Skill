# Focused testing reference

## Pytest basics

Statsmodels uses pytest. Focused commands generally follow:

```bash
pytest statsmodels/regression/tests/test_regression.py -q
pytest statsmodels/tsa/tests/test_stattools.py -q
pytest statsmodels/stats/tests/test_diagnostic.py -q
```

When running from a source checkout, make sure the package has been built/editably installed in the environment that runs pytest.

## Changed-path mapping

| Changed path | Start with |
| --- | --- |
| `statsmodels/regression/` | `statsmodels/regression/tests/` plus affected examples/docs. |
| `statsmodels/genmod/` | `statsmodels/genmod/tests/`. |
| `statsmodels/discrete/` or `miscmodels/ordinal_model.py` | `statsmodels/discrete/tests/` and ordinal model tests. |
| `statsmodels/tsa/` | nearest `statsmodels/tsa/tests/test_*.py`; add state-space/vector tests when relevant. |
| `statsmodels/stats/` | nearest `statsmodels/stats/tests/test_*.py`. |
| `statsmodels/graphics/` | `statsmodels/graphics/tests/` with headless matplotlib. |
| `statsmodels/datasets/`, `iolib/`, `tools/` | corresponding subpackage tests. |
| `docs/` or `examples/` | docs/example-specific checks; run package tests only if code behavior changed. |
| `pyproject.toml`, build metadata, Cython templates | source build/import smoke plus affected compiled-extension tests. |

## Markers and runtime control

The project uses markers for examples, matplotlib, slow tests, high memory, low precision, polars, joblib, and related surfaces. Prefer safe focused subsets over broad marker changes. If a pytest plugin configured in project metadata is missing, either install the test extra or override/add a documented reason; do not assume failures are model regressions.

## Suggested progression

1. Import smoke: `python -c "import statsmodels.api as sm; print(sm.OLS)"`.
2. Focused module tests for changed files.
3. Example or docs smoke if user-facing examples changed.
4. Broader subpackage tests when a shared base/result class changed.
5. Full suite only for release-level or cross-cutting changes.
