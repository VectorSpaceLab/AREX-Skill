# Nilearn Development Guide

Use this guide for code, API, architecture, changelog, and PR-handoff changes
inside the Nilearn source checkout.

## Environment and Command Basics

- Nilearn is a Python package requiring Python `>=3.10`.
- Development installs use dependency groups. Typical local setup is
  `uv sync` or `python -m pip install -e . --group dev`; plotting-specific work
  also needs the `plotting` extra or plotting dependency group used by tox.
- The package exposes no console scripts in metadata; invoke maintenance helpers
  as Python files or through `tox` environments.
- Prefer targeted commands during agent work. Escalate to full `tox -e latest`,
  `tox -e plotting`, `tox -e min`, or `pre-commit run --all-files` only when the
  change warrants the runtime.

## Style Rules

- Follow PEP8 and existing Nilearn style.
- Python formatting is ruff-managed with 4-space indentation, double quotes, and
  `line-length = 79`.
- Use clear `snake_case` names for functions and variables, `CamelCase` for
  classes, and leading `_` for private implementation details.
- Use absolute imports for internal Nilearn modules. Do not add relative imports.
- Keep functions short and focused when practical; avoid broad cleanup around a
  surgical bug fix.
- Do not add a new top-level dependency without prior human discussion.
- Public functions/classes need NumPy-style docstrings. Document parameter types
  and defaults as `type, default=value` rather than prose such as "Defaults to".

## Import-Linter Architecture

Nilearn enforces layered imports through `pyproject.toml`. Before adding an
import, identify the source module and imported module layer.

| Layer | Packages | Rule of thumb |
| --- | --- | --- |
| Top utility | `nilearn.utils` | Public convenience layer; do not use as a shared lower-level dependency. |
| Top estimators | `nilearn.glm`, `nilearn.decoding`, `nilearn.connectome`, `nilearn.decomposition` | These must not import peer top estimator packages. |
| Mass univariate | `nilearn.mass_univariate` | Imported only by allowed higher layers such as `glm`; avoid new callers. |
| Mid layer | `nilearn.maskers`, `nilearn.image`, `nilearn.surface`, `nilearn.plotting`, `nilearn.masking`, `nilearn.reporting`, `nilearn.datasets`, `nilearn.interfaces` | Mid-layer packages may import within this layer and lower layers. |
| Signal | `nilearn.signal` | Lower-level time-series preprocessing; do not import higher image/masker/plotting packages. |
| Base | `nilearn._base` | Base estimator support; keep dependencies minimal. |
| Core | `nilearn.nilearn_typing`, `nilearn.exceptions`, `nilearn._utils.versions` | Lowest-level typing, exceptions, and version helpers. |

Additional contracts include:

- `nilearn.connectome` is restricted to lower dependencies, especially
  `nilearn.signal`, with test-only exceptions.
- Fixtures in `nilearn.conftest` must not depend on `nilearn._utils.data_gen`.
- `nilearn.mass_univariate` is protected and should only be imported by allowed
  importers.
- `nilearn._assets` is protected for reporting, plotting, and a legacy GLM path.
- Tests have explicit import exceptions, but production code should not rely on
  test-only exemptions.

If an import-linter failure appears, prefer moving shared helpers downward,
passing data through public APIs, or adding a local minimal helper over adding a
new architecture exception.

## Public API and Backward Compatibility

- Preserve existing public import paths unless a deprecation path is approved.
- Public objects exposed through package `__init__.py` files should remain stable.
- Keep private helpers private. A leading underscore means implementation detail;
  modules also use `__all__` to define what is public.
- Use deprecation warnings before removing or renaming public parameters,
  attributes, functions, or modules.
- For deprecated parameter migration, follow existing helpers and tests around
  `_warn_deprecated_params` and `transfer_deprecated_param_vals`.
- When a public docstring changes behavior or introduces an API, add
  `.. nilearn_versionadded::` or `.. nilearn_versionchanged::` with the current
  development version style used in the repo.

## Estimator Conventions

Nilearn estimators follow scikit-learn patterns while accepting neuroimaging
inputs such as Niimg-like objects and surface images.

- Constructors should store parameters without doing data validation or fitting.
- `fit(...)` returns `self` and overwrites fitted state on repeated calls.
- Learned attributes end in trailing underscore, such as `mask_img_`, `labels_`,
  `components_`, `coef_`, or report-related fitted attributes.
- Methods that require fitting should use fitted-state checks consistent with
  existing estimators.
- Transformers expose `transform` and often `fit_transform`; inverse operations
  should preserve documented shapes and output types.
- Maskers, decomposition estimators, decoding estimators, GLM models, and
  connectivity estimators may need both scikit-learn estimator checks and
  Nilearn-specific checks from the estimator-check utilities.
- If a new estimator intentionally fails a scikit-learn check because image input
  semantics differ from array-only estimators, update expected-failure handling
  and add a Nilearn-specific replacement check.

## Changelog and PR Notes

For PR-worthy changes, update `doc/changes/latest.rst` with one single-line
entry in the appropriate section. Use one of the accepted badges:

| Badge label | Use for |
| --- | --- |
| Doc | Documentation-only changes. |
| Maint | Maintenance, CI, dependencies, or tooling. |
| API | Public API additions or behavior changes. |
| Plotting | Plotting or visualization behavior. |
| Test | Test-only changes. |
| Deprecation | Deprecations or removals. |
| Code | Internal code or bug fixes not covered above. |

Accepted badge literals:

```rst
:bdg-primary:`Doc`
:bdg-secondary:`Maint`
:bdg-success:`API`
:bdg-info:`Plotting`
:bdg-warning:`Test`
:bdg-danger:`Deprecation`
:bdg-dark:`Code`
```

Entry shape:

```rst
- :bdg-dark:`Code` Briefly describe the change (:gh:`PR_NUMBER` by `Author`_).
```

If no PR number or author is known during local agent work, leave a clear
placeholder only if the repository's human workflow expects it; otherwise note
in the handoff that the changelog entry needs final PR metadata.

## Maintenance Tool Inventory

Useful checked-in helpers include:

- `maint_tools/check_docstrings.py` and
  `maint_tools/missing_default_in_docstring.py` for docstring quality.
- `maint_tools/check_atlas.py` for atlas metadata/downloader maintenance; this
  may involve network-like dataset behavior and is not a default safe check.
- `maint_tools/check_private.py` for private/public API consistency.
- `maint_tools/citation_cff_maint.py` for keeping citation authors and docs in
  sync.
- `maint_tools/check_gha_workflow.py` for GitHub Actions workflow checks.
- `build_tools/github/restrict_tests_to_run.py` for CI test-selection logic.

Do not reference these source paths from public user-facing Nilearn workflows;
inside this development-maintenance skill they are evidence and maintainer
orientation only.
