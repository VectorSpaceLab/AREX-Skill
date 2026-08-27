# Nilearn Development Troubleshooting

Use this matrix when validation fails during Nilearn source maintenance.

## Failure Matrix

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| `import-linter` reports a layer violation | New import crosses Nilearn architecture boundaries | Move shared code to an allowed lower layer, invert the dependency, pass data through an existing public API, or use a small local helper. Do not add an exception first. |
| Top modules import each other | `glm`, `decoding`, `connectome`, or `decomposition` gained a peer dependency | Extract shared behavior downward or keep integration in tests/docs rather than production imports. |
| `nilearn.connectome` forbidden-import failure | Connectome imported image, maskers, plotting, reporting, datasets, or mass-univariate code | Keep connectome logic array/signal based; move neuroimaging conversions outside connectome. |
| `nilearn.conftest` import failure involving `data_gen` | Shared fixtures depend on generated-data utilities forbidden by architecture | Inline tiny fixture generation or place specialized helpers in package-local tests instead of global conftest. |
| Ruff line-length or quote failures | Code conflicts with `line-length = 79` or double-quote formatting | Run ruff formatting/checks on changed files; split expressions before adding ignores. |
| Strict pytest marker error | A marker is not registered in config | Use registered markers only: `slow`, `single_process`, `thread_unsafe`, `ai_generated`, `engines`, `mpl_image_compare`, or plugin-provided marks already used in the repo. |
| Missing `@pytest.mark.ai_generated` | Agent generated or modified a test without marker | Add `@pytest.mark.ai_generated` to the generated/modified test function, class, or module scope. |
| Test downloads data or hits network | Dataset fetcher path lacks mocking or cache isolation | Prefer mocked request fixtures and temp data dirs; skip network-style checks unless downloader behavior is the task. |
| Optional plotting import failure | Environment lacks `matplotlib`, `plotly`, or `kaleido` | Use `tox -e plotting -- <path>` or install plotting extras for plotting/reporting tests. For non-plotting changes, choose non-plotting tests. |
| Plotly/kaleido export failure mentions browser/Chrome | Image export backend needs browser support | Avoid export assertions unless export is the behavior under test; otherwise document the environment requirement for human validation. |
| Baseline image comparison fails | Rendering changed or matplotlib version differs from baseline assumptions | First confirm whether the change should affect pixels. If not, use semantic assertions. Regenerate baselines only with explicit maintainer intent. |
| `pytest_mpl` finds no baseline or writes results | Baseline paths or `--mpl` flags are wrong | Use the tox `pytest_mpl` environment for comparisons. Do not hand-roll baseline paths unless maintaining the visual test suite. |
| Estimator check says fitted attributes missing | `fit` did not create expected trailing-underscore state | Ensure `fit` returns `self` and sets/overwrites all learned attributes with `_` suffix. |
| Estimator clone/get-params failure | Constructor mutates inputs, validates data, or hides parameters | Keep `__init__` parameter-only and validation in `fit` or called methods. |
| Estimator check mismatch on array inputs | Nilearn estimator expects Niimg/surface semantics | Add or update expected-failure rationale only if intentional, and cover the behavior with a Nilearn-specific check. |
| Warnings become errors in tox | Tests emit `FutureWarning` or scikit-learn `ConvergenceWarning` | Assert the warning explicitly if expected, or update code to avoid it. Do not globally silence warnings. |
| `pre-commit` modifies files | Formatter or generated metadata changed staged files | Review the diff, keep intended changes, and rerun the specific hook on changed files. |
| Docstring quality check fails | Numpydoc sections, defaults, or version directives are incomplete | Document every public parameter default, return shape/type, and version change in NumPy format. |
| Changelog lint or reviewer complaint | Entry lacks badge, category, PR link, or author | Use one single-line entry in `doc/changes/latest.rst` with an accepted badge and final PR metadata. |

## Import-Linter Debug Steps

1. Identify the source module and imported module named in the failure.
2. Map both modules to the architecture table in the development guide.
3. If the import points upward or sideways across a forbidden boundary, remove
   the import from production code.
4. Prefer one of these fixes:
   - Move a pure helper to `nilearn._base`, `nilearn.signal`, or a narrower
     allowed lower module only when it truly belongs there.
   - Make the higher-level caller pass precomputed values into the lower layer.
   - Keep optional visualization/reporting imports inside plotting/reporting
     modules rather than lower image, signal, or connectome modules.
   - Add tests under package test directories when only test code needs the
     higher-level helper.
5. Treat import-linter ignore-list changes as last-resort architecture changes
   requiring human review.

## Optional Plotting and Reporting Issues

- If matplotlib is missing, Nilearn skips or ignores plotting/reporting paths in
  collection. Do not diagnose unrelated non-plotting failures by installing
  plotting unless the changed behavior needs it.
- If matplotlib is newer than the minimum supported version, baseline comparison
  tests may be ignored because baselines are intended for the oldest supported
  plotting stack.
- Always close figures in new tests or rely on the existing autouse fixture.
- For HTML/report tests, prefer deterministic string, object, or file-existence
  assertions over screenshot comparisons.

## Network and Dataset Fetcher Issues

- Nilearn has many dataset fetchers, but default agent validation should remain
  no-network.
- For downloader changes, search existing dataset tests for request mocks,
  temporary Nilearn data directories, and retry/error fixtures.
- Do not use real user cache directories in tests. Use temporary paths.
- Keep tests tiny and deterministic; avoid full atlas or OpenNeuro downloads
  unless the user explicitly asks for an integration check.

## Pre-Commit and Lint Issues

Useful targeted commands:

```bash
pre-commit run ruff-format --files <changed.py>
pre-commit run ruff-check --files <changed.py>
pre-commit run import-linter --files pyproject.toml
pre-commit run doc8 --files <changed.rst>
pre-commit run codespell --files <changed files>
```

Some hooks run against repository state rather than only the passed file. If a
hook reports unrelated historical failures, do not fix them unless they are in
scope; record them in the handoff.

## When to Broaden Validation

Broaden beyond targeted tests when:

- A public API signature, default, deprecation, or import path changed.
- A base class, shared fixture, or estimator-check utility changed.
- An import architecture boundary changed.
- A dependency, tox, pre-commit, or pyproject setting changed.
- Plotting/reporting behavior changed across both static and interactive paths.

Avoid broad validation during quick iteration when the change is isolated and a
specific failing test already covers the behavior.
