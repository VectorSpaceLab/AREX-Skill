# Repository provenance

```yaml
schema: disco.repo-provenance.v1
skill_id: statsmodels
source:
  vcs: git
  remote_url: https://github.com/statsmodels/statsmodels.git
  branch: main
  commit: 4518048df0f4cbb0dd326ac578e1b1cdabc98a57
  exact_tag: null
  describe: 4518048
  dirty_state: dirty-untracked-skill-artifacts-only
package:
  distribution_name: statsmodels
  import_name: statsmodels
  inspected_version: 0.1.dev1+g4518048df
  declared_python: ">=3.10"
  required_backend: cpu
  optional_surfaces:
    - matplotlib graphics
    - pytest test suite
    - joblib distributed estimation
    - polars compatibility
    - external X-13/X-12 executable for selected time-series functions
```

## Evidence paths used

- `pyproject.toml`, `meson.build`, `requirements.txt`, `requirements-dev.txt`, `requirements-doc.txt`
- `README.rst`, `INSTALL.txt`, `CONTRIBUTING.rst`
- `docs/source/api.rst`, `docs/source/api-structure.rst`, `docs/source/user-guide.rst`, `docs/source/gettingstarted.rst`, `docs/source/endog_exog.rst`, `docs/source/missing.rst`, `docs/source/pitfalls.rst`, `docs/source/install.rst`
- Topic docs: `docs/source/regression.rst`, `glm.rst`, `gee.rst`, `gam.rst`, `rlm.rst`, `mixed_linear.rst`, `discretemod.rst`, `tsa.rst`, `statespace.rst`, `vector_ar.rst`, `stats.rst`, `diagnostic.rst`, `graphics.rst`, `datasets/index.rst`, `dev/test_notes.rst`, `dev/testing.rst`, `dev/warnings-and-exceptions.rst`
- Public source roots under `statsmodels/`, with `archive/`, generated build/cache output, and most experimental `sandbox/` material excluded from runtime guidance
- Representative examples under `examples/python/` and behavior tests under `statsmodels/*/tests/`
- Maintainer scripts: `tools/check_api.py`, `tools/validate_docstrings.py`, `tools/export_notebooks_to_python.py`, `tools/nbgenerate.py` as reference-only evidence

## Refresh triggers

Refresh this skill when statsmodels changes public model constructors, formula wrappers, time-series API names, result object methods, optional dependency policy, build system requirements, test marker policy, or documented warnings/pitfalls. A dirty state containing only generated `skills/` output does not change the source evidence baseline.
