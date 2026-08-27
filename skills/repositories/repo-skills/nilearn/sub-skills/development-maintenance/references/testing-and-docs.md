# Nilearn Testing and Documentation Guide

Use this guide to choose safe validation for focused Nilearn changes. Prefer the
smallest command that exercises the changed behavior, then broaden only if the
change crosses modules or public contracts.

## Fast Test Selection

Start from changed paths:

| Changed path | First targeted checks |
| --- | --- |
| `nilearn/image/*.py` | `tox -e latest -- nilearn/image/tests/test_<module>.py` |
| `nilearn/masking.py` | `tox -e latest -- nilearn/tests/test_masking.py` and nearby masker tests if needed |
| `nilearn/maskers/*.py` | `tox -e latest -- nilearn/maskers/tests/test_<module>.py` |
| `nilearn/surface/*.py` | `tox -e latest -- nilearn/surface/tests/` or the matching test file |
| `nilearn/glm/**` | `tox -e latest -- nilearn/glm/tests/<matching-test>.py` |
| `nilearn/decoding/**` | `tox -e latest -- nilearn/decoding/tests/<matching-test>.py` |
| `nilearn/connectome/**` | `tox -e latest -- nilearn/connectome/tests/<matching-test>.py` |
| `nilearn/decomposition/**` | `tox -e latest -- nilearn/decomposition/tests/<matching-test>.py` |
| `nilearn/plotting/**` | `tox -e plotting -- nilearn/plotting/<area>/tests/<matching-test>.py` or safe non-baseline plotting tests |
| `nilearn/reporting/**` | `tox -e plotting -- nilearn/reporting/tests/<matching-test>.py` |
| `doc/**/*.rst` | relevant doctest, `tox -e test_doc -- <doc path>`, or `tox -e doc -- html` for broad doc changes |
| `examples/**/*.py` | run the example only if needed and safe; avoid dataset-heavy examples by default |
| `pyproject.toml`, `tox.ini`, `.pre-commit-config.yaml` | targeted `pre-commit` hook or `tox list`; broaden to full pre-commit only near handoff |

The bundled script suggests commands without running them:

```bash
python ../scripts/select_safe_tests.py nilearn/maskers/nifti_masker.py
```

It accepts paths as CLI arguments or newline-separated stdin.

## Pytest and Tox Commands

- `tox -e latest -- <path>` runs tests with latest supported dependencies and no
  plotting extra by default.
- `tox -e plotting -- <path>` includes plotting dependencies and doc tests.
- `tox -e min -- <path>` checks minimum supported runtime dependencies.
- `tox -e plot_min -- <path>` checks minimum dependencies with plotting.
- `tox -e flaky -- <path>` runs tests marked `flaky` or `single_process`.
- `tox -e pytest_mpl -- <path>` compares baseline images; do not run by default.
- `tox -e pytest_mpl_generate` regenerates visual baselines; this is a deliberate
  maintainer action, not a routine validation step.
- `tox -e doc_qc` runs docstring quality helpers.
- `tox -e doc` or `tox -e doc_latest` builds documentation and may take much
  longer than unit tests.
- `pre-commit run --files <changed files>` is preferable during focused work;
  reserve `pre-commit run --all-files` for final broad validation or explicit
  user request.

The default `latest` tox command excludes `slow`, `flaky`, and `single_process`
markers in the first pass and then runs slow tests separately. For agent work,
pass a specific file or test node after `--`.

## Required Test Marker for Agent Changes

Any test generated or modified by an AI coding agent must include:

```python
@pytest.mark.ai_generated
```

Place it directly on the test function or on a test class/module when every
contained test was generated or modified. Import `pytest` if the test file does
not already import it. The marker is registered in pytest config, so strict
marker mode accepts it.

Do not mark untouched existing tests merely because adjacent code changed.

## Fixtures and Synthetic Data

- Prefer tiny generated arrays, `nibabel.Nifti1Image`, and in-memory surface data.
- Reuse fixtures from `nilearn/conftest.py`, including seeded random generators,
  affine helpers, image-shape helpers, NIfTI image fixtures, and surface fixtures.
- Use the `rng` fixture or `numpy.random.default_rng(seed)` for deterministic
  tests.
- Look for module-local `conftest.py` fixtures before adding new shared fixtures.
- Shared fixtures in `nilearn.conftest` must stay independent of
  `nilearn._utils.data_gen` because an import-linter contract enforces this.
- Dataset fetchers and network-like tests should use existing mocks or be skipped
  unless the task explicitly concerns downloader behavior.

## Estimator Checks

For estimator changes:

- Run the matching module tests first.
- Find the estimator compatibility test file in the same package, commonly named
  around `test_*estimators*`, `test_same_api`, or sklearn compatibility.
- Use expected-failure maps only for known incompatibilities; pair them with a
  Nilearn-specific replacement check where possible.
- Preserve `fit` returning `self`, fitted attributes ending in `_`, cloneability,
  parameter introspection, and output shape/type contracts.
- Slow estimator-check suites may be marked `slow`; run only the relevant node
  while iterating.

## Plotting, Reporting, and Baselines

Plotting and reporting tests need extra care:

- Use `tox -e plotting -- <specific test file or node>` for matplotlib/plotly
  behavior.
- Nilearn configures matplotlib to use the non-interactive `Agg` backend during
  tests and closes figures after each test.
- Avoid baseline image comparisons unless the change intentionally affects figure
  rendering. Baseline tests are version-sensitive and run through `pytest-mpl`.
- Do not regenerate baseline images unless a maintainer explicitly requests it.
- Prefer semantic assertions on display objects, warnings, axes content, HTML
  snippets, or file creation over pixel comparisons for bug fixes.
- Plotly/kaleido image export may require a browser runtime; do not treat that as
  a default local requirement for non-export tests.

## Documentation and Gallery Work

- Public APIs need NumPy-style docstrings with complete parameter defaults,
  return values, and examples only when appropriate.
- New or changed public behavior should include `.. nilearn_versionadded::` or
  `.. nilearn_versionchanged::` directives in the style already used in Nilearn.
- Gallery examples must be didactic, lightweight, and avoid heavy downloads.
- Documentation builds can run maintenance helpers that update citation/name
  files; check for unintended generated changes before handoff.
- Link syntax should use Nilearn's documented roles when editing source docs,
  but generated skill content should remain self-contained and not depend on
  source documentation paths.

## Safe Escalation Pattern

1. Run or recommend the exact test node covering the changed line.
2. Add related estimator, docstring, or plotting checks only if the change touches
   those contracts.
3. Run a package-level test folder if multiple files in that package changed.
4. Run `pre-commit run --files <changed files>` for style/import/doc lint.
5. Suggest full tox/pre-commit only when cross-package architecture, dependency,
   or public API changes justify it.
