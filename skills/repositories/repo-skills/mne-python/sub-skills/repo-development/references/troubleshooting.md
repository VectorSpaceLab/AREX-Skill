# Repository-development troubleshooting

Use this reference when a MNE-Python maintenance task fails locally or in CI. Pair it with [contributor workflows](contributor-workflows.md) and [API surface rules](api-surface-and-docs.md).

## `import mne` resolves to the wrong package

Symptoms:

- a local edit appears to have no effect;
- signatures or behavior differ from the edited file;
- tests import a site-packages install rather than the checkout;
- `mne.__file__` points outside the intended repository.

Checks:

```bash
python -c "import mne; print(mne.__file__)"
python skills/disco/mne-python/sub-skills/repo-development/scripts/check_mne_checkout.py --repo-root .
```

Fixes:

- install the checkout in editable mode in the active environment;
- run commands from the intended repo root;
- remove stale `PYTHONPATH` entries that point at another checkout;
- restart the Python process after changing installation state;
- avoid mixing multiple MNE-Python checkouts in one shell session.

## Optional dependency failures

Symptoms:

- `ModuleNotFoundError` for packages such as scikit-learn, pandas, nibabel, PyVista, Qt bindings, pybv, snirf, h5io, or pymatreader;
- import-nesting failures after adding a top-level optional import;
- tests skip unexpectedly because an optional dependency is absent.

Fixes:

- Install the optional group or dependency that matches the edited feature, not an unrelated broad stack.
- Move optional/heavy imports inside the function or method that uses them.
- Use local `pytest.importorskip(...)` or equivalent skip logic in tests that require optional packages.
- Re-run the focused test and, for import-boundary edits, `make nesting`.

## Dataset-dependent tests fail or hang

Symptoms:

- missing testing/sample dataset;
- network fetch failures;
- long-running tests unexpectedly downloading data;
- tests skipped by data-availability guards.

Fixes:

```bash
python -c "import mne; mne.datasets.testing.data_path(verbose=True)"
python -c "import mne; mne.datasets.sample.data_path(verbose=True)"
```

Guidance:

- Prefer tests built on synthetic data or the small `testing` dataset.
- Do not require the large `sample` dataset for a new small unit test unless the feature genuinely needs it.
- If network or data access is unavailable, report the skipped/blocked data condition rather than pretending the full test ran.

## Documentation builds warn or fail

Symptoms:

- Sphinx warnings unrelated to the current patch;
- stale generated files in the docs build output;
- gallery examples taking too long or requiring unavailable data/display;
- cross-reference warnings for new public endpoints.

Fixes:

```bash
make -C doc clean
make -C doc html-noplot
PATTERN=<regex> make -C doc html-pattern
make test-doc
```

Guidance:

- Use `html-noplot` for formatting/linking checks that do not need to execute examples/tutorials.
- Use `html-pattern` only for the changed example/tutorial pattern.
- Full docs builds can be expensive; run them only when the docs scope justifies it or a human maintainer asks.
- If a public API cross-reference fails, confirm the endpoint appears on the appropriate `doc/api/*.rst` thematic page.

## Changelog name failures

Symptoms:

- changelog check reports a credited name without a link target;
- docs build reports unresolved name references;
- duplicate contributor targets disagree on URL;
- new contributor uses ordinary name-reference syntax or existing contributor uses `:newcontrib:` incorrectly.

Fixes:

- Add a matching target to `doc/changes/names.inc` for every credited person.
- Keep one URL per normalized contributor name.
- Use `:newcontrib:` only for first-time contributors.
- Use a normal reST name reference for existing contributors.
- Keep changelog fragments under `doc/changes/dev/<PR-number>.<type>.rst` and do not edit aggregate changelogs for new changes.

## Docstring validation fails

Symptoms:

- parameter mismatch errors from `mne/tests/test_docstring_parameters.py`;
- errors saying a type description includes `optional` or a default;
- public function/class missing from API docs;
- `verbose` default is not `None`;
- type-hint/docstring mismatches.

Fixes:

- Align signature and docstring parameter names exactly.
- Remove `optional` and default values from parameter type fields; describe defaults in prose if needed.
- Use `str | None` style for unions in docstrings.
- Add public endpoints to the appropriate `doc/api/*.rst` autosummary page.
- For public `verbose`, default to `None` unless an established exception applies.
- Re-run:

  ```bash
  pytest mne/tests/test_docstring_parameters.py
  make ruff
  ```

## Deprecation warning tests fail

Symptoms:

- `pytest.warns(FutureWarning, ...)` does not catch the warning;
- warning text is too broad or changed unexpectedly;
- internal call sites still trigger deprecation warnings;
- a deprecated parameter branch handles simultaneous old and new parameters incorrectly.

Fixes:

- Use `mne.utils.deprecated` for functions/classes and `mne.utils.warn(..., FutureWarning)` for parameters.
- Assert each expected branch with a focused warning test.
- Search and update internal callers immediately.
- Keep behavior for ambiguous calls explicit, especially when both old and new parameter names are supplied.
- Add an `apichange` changelog fragment when a deprecation cycle changes user-facing behavior.

## Import-nesting failures

Symptoms:

- `make nesting` fails after adding an import;
- importing `mne` or a subpackage loads optional GUI, plotting, stats, or I/O dependencies too early;
- startup time or minimal install behavior regresses.

Fixes:

- Move optional imports into the function/method path where they are required.
- Use lightweight standard-library or required-dependency imports at module level only when needed.
- Avoid public package stubs that force optional modules during import.
- Re-run `make nesting` and a minimal `python -c "import mne"` check.

## Pre-commit or style failures

Symptoms:

- ruff/import-format/docstring style failures;
- codespell, rstcheck, yamllint, toml-sort, or other pre-commit hook errors;
- large unrelated diffs after formatting.

Fixes:

```bash
make ruff
```

Guidance:

- Review all automated edits before continuing.
- Do not include broad unrelated formatting in a targeted bug fix.
- Keep generated or formatting-only changes separate when the human maintainer asks for review-friendly commits.

## AI-policy or license blockers

Symptoms:

- user asks to submit an AI-generated issue/PR/comment verbatim;
- generated code closely follows a specialized algorithm from a source with unclear or incompatible license;
- user wants to skip human review/testing/disclosure.

Response:

- Decline to produce ready-to-submit issue/PR text; provide technical notes for a human to rewrite.
- Do not adapt code with unknown, GPL/LGPL/AGPL, non-commercial, or no-derivatives licensing.
- Require human review, understanding, testing, and AI-assistance disclosure before submission.
- If outside code is BSD-compatible and adapted, include an attribution comment directly above the adapted code.

## Source-path naming mismatch in old messages

Some source guidance refers generically to `doc/python_reference.rst`, while the inspected tree stores the API reference under `doc/api/python_reference.rst` with thematic pages in the same directory. When operating on a current checkout, inspect the local tree and update the actual API page used by that checkout.
