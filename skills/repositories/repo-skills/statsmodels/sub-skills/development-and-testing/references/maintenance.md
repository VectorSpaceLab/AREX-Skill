# statsmodels maintenance reference

## Source build/editable install

Statsmodels uses Meson and Cython for compiled extensions. A source checkout must be built before import checks can validate compiled modules.

Typical source workflow:

```bash
python -m pip install -e . --no-build-isolation
python -c "import statsmodels, statsmodels.api as sm; print(statsmodels.__version__, sm.OLS)"
```

If Cython files or templates change, rebuild/reinstall before running tests. Prefer a dedicated development environment; do not mutate a user's base environment without approval.

## Public API and docs evidence

The repository exposes public API through `statsmodels.api`, `statsmodels.formula.api`, subpackage `api.py` files, and topic docs. Public API maintenance should check:

- The object imports from the documented API path.
- The direct module import remains valid for library users.
- Autosummary/docs references match the object path.
- New warnings or deprecations follow the repo's warning policy.

## Maintainer tools (reference-only)

The source tree contains useful maintainer tools such as API checks, docstring validation, and notebook-to-Python export helpers. They are tied to the checkout and docs build environment, so this generated skill does not copy them as runtime scripts. Use them only inside a statsmodels source checkout after reading their help/source and understanding side effects.

| Source maintainer surface | Use | Runtime decision |
| --- | --- | --- |
| API check tooling | Detect public API drift | Reference-only; use focused imports in this skill. |
| Docstring validator | Validate numpydoc-style docs | Reference-only; requires docs/dev dependencies. |
| Notebook/example generators | Build docs examples | Reference-only; can mutate generated files. |
| CI and release tooling | Project automation | Excluded from runtime guidance due to environment/release side effects. |

## Archive and sandbox cautions

`archive/` is deprecated legacy code and excluded from modern lint scope. `sandbox/` contains experimental code at varied maturity. Do not treat either as stable production API unless the user specifically asks and accepts the risk.
