# API surface, lazy stubs, and documentation rules

Use this reference when a repository edit adds, moves, renames, deprecates, or documents MNE-Python public API. For command selection and policy notes, pair it with [contributor workflows](contributor-workflows.md). For failures, see [troubleshooting](troubleshooting.md).

## Public API model

MNE-Python uses lazy public APIs. The inspected root package initializes `__getattr__`, `__dir__`, and `__all__` through `lazy_loader.attach_stub(__name__, __file__)`. The `.pyi` stub file beside an `__init__.py` is therefore the source of truth for exported names and lazy imports.

Operational consequences:

- Do not add a public function/class only to an implementation module and assume `import mne` or `import mne.subpackage` will expose it.
- When a public name should be available from a package namespace, update the corresponding `__init__.pyi`:
  - add the name to `__all__`;
  - add the import line that resolves the name from its implementation module;
  - keep imports ordered and formatted consistently with the existing stub.
- Many subpackages follow the same `__init__.py` plus `__init__.pyi` lazy-loader pattern. Inspect the package being edited, not only the root package.
- The source generator for `.pyi` files is mutating and dev-dependency-sensitive. If a human maintainer chooses to use generated stubs, still review the resulting `.pyi`, implementation, API docs, tests, and changelog together.

## Public API addition checklist

For a new public endpoint, verify each layer explicitly:

1. **Implementation**: add the function/class/method in the appropriate module, following local naming, import, mutation, and optional-dependency patterns.
2. **Namespace exposure**: if it should be importable from `mne` or a subpackage namespace, update the relevant `__init__.pyi` and `__all__` entry.
3. **Docstring**: write a numpydoc-style docstring with MNE deviations listed below.
4. **API reference**: add the endpoint to the appropriate `doc/api/*.rst` autosummary page so cross-references can resolve.
5. **Tests**: add or update compact tests, preferably in an existing nearby test file.
6. **Changelog**: add a `doc/changes/dev/<PR-number>.<type>.rst` fragment for user-facing changes and ensure credited names resolve.
7. **Verification**: run focused tests plus the API/docstring checks relevant to the change.

Minimal import check after changing a public namespace:

```bash
python - <<'PY'
import mne
print(mne.__file__)
print(hasattr(mne, "NEW_PUBLIC_NAME"))
PY
```

Use the real endpoint name in place of `NEW_PUBLIC_NAME`.

## API reference and cross-reference rules

- The API reference root is under `doc/api/`; the inspected `doc/api/python_reference.rst` includes thematic API pages such as `most_used_classes`, `file_io`, `preprocessing`, `visualization`, `statistics`, and others.
- Public classes/functions/methods must appear on the appropriate thematic API page, not merely in prose, for cross-references to resolve reliably.
- Source tests collect documented public names from `doc/api/*.rst` autosummary blocks and fail if public functions/classes are missing.
- Prefer Sphinx roles for public endpoints: `:func:`, `:class:`, `:meth:`, `:attr:`, `:mod:`, and `:ref:`. Changelog entries should reference public endpoints rather than private internals.
- Be careful with multiple exposure points. Cross-references should match the documented public location, not an undocumented alias.

Focused checks:

```bash
pytest mne/tests/test_docstring_parameters.py
make ruff
```

If docs pages or examples/tutorials changed, add one of:

```bash
make -C doc html-noplot
PATTERN=<regex> make -C doc html-pattern
make test-doc
```

## Numpydoc conventions used by MNE-Python

MNE mostly follows NumPy docstring style with local deviations:

- Do not put `optional` or default values in parameter type fields. Defaults belong in the parameter description or are evident from the signature.
- Use pipe syntax for multiple possible types, for example `str | None`, not `str or None`.
- Do not add `Raises` or `Warns` sections.
- Use `sphinxcontrib-bibtex` citation roles such as `:footcite:` and `footbibliography::` when adding scholarly references. Reference keys must follow the project style.
- Give return values informative names.
- Public functions or methods with a `verbose` parameter should default to `verbose=None` unless an established exception exists.
- For typed modules, type hints and rendered docstring types are checked against each other.

Docstring validation catches common problems:

- signature parameters missing from the docstring or extra docstring parameters;
- `optional` or `default` text in parameter type fields;
- public functions/classes not listed in API docs;
- type-hint/docstring mismatches in strictly typed modules;
- stale allowances for malformed docstring types.

## Shared docstrings and `fill_doc`

Common parameter text is centralized in `mne.utils.docs` and inserted with the `@fill_doc` decorator plus placeholders. Before writing a long parameter description manually:

1. Search for an existing `docdict` entry or placeholder name.
2. Reuse the shared entry if it matches.
3. Add a new shared entry only when it is broadly reusable and tested by the docstring suite.
4. Keep placeholder spelling exactly aligned with the shared dictionary.

## Optional dependencies and import nesting

MNE-Python keeps import time and hard requirements low. For optional or heavy dependencies:

- import lazily inside the function/method that needs the dependency;
- provide actionable error messages when a missing dependency blocks a feature;
- avoid exposing optional imports through lazy package stubs unless the dependency is required for the public namespace itself;
- add tests that either install the dependency or skip/importorskip locally;
- run import-nesting checks for changes that could pull optional dependencies into import time.

Focused check:

```bash
make nesting
```

## Deprecating or moving API

- Use `mne.utils.deprecated` for functions/classes.
- Use `mne.utils.warn(..., FutureWarning)` for parameter deprecations.
- Write tests with `pytest.warns(FutureWarning, match=...)` for every deprecation branch.
- Update internal call sites immediately.
- Changelog type is usually `apichange` when a deprecation cycle is involved.
- Do not remove a public endpoint without the human maintainer confirming the release-stage context.

## Visualization API pattern

For visualization features:

- add a public function under `mne.viz`;
- have object methods call the public function, not the reverse;
- include a `show` boolean parameter;
- return a Matplotlib figure/list or the appropriate 3D visualization object;
- default to `RdBu_r` for signed, zero-centered data and `Reds` otherwise;
- document and test headless behavior when practical.

## Public API hard-case workflow

When asked to add a new public function, a safe answer should identify all required follow-up files before editing:

```text
implementation module -> package __init__.pyi -> doc/api thematic page -> focused tests -> changelog fragment -> names.inc if credited -> docstring/API checks
```

If any link in that chain is missing, do not claim the API addition is complete. State the missing layer and ask the human maintainer for the needed decision, such as the PR number for the changelog fragment or whether the endpoint should be public at all.
