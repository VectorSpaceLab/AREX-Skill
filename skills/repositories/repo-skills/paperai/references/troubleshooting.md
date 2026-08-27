# Cross-cutting troubleshooting

## Install and import

- **`ModuleNotFoundError` for `txtai`, `txtmarker`, or `staticvectors`:** install
  the declared `paperai` package in the active environment and run
  `python -m pip check`. Do not mix a package from one Python with a CLI from
  another.
- **Import works but model load fails:** import checks do not load weights. Check
  the selected txtai model reference, cache/network permissions, device choice,
  and available memory separately.
- **Dependency conflicts:** prefer a fresh Python 3.10+ environment instead of
  mutating a user-owned environment. Install only optional UI/API/annotation
  dependencies required by the selected workflow.

## Corpus and configuration

- **SQLite errors or zero rows:** check that the user-owned model directory has
  `articles.sqlite` with the expected `articles`/`sections` schema and tagged
  articles. Use the indexing route's `inspect_corpus.py` before building a
  model.
- **YAML errors:** use the reporting validator for task shape and PyYAML parsing;
  then distinguish schema validity from txtai option/model validity.
- **Missing model files:** the directory must contain saved txtai artifacts in
  addition to the database. Re-index only after preserving any useful existing
  model.

## CLI/API behavior

- The module entry points are positional and have limited help behavior; a
  missing argument may surface as a low-level `TypeError`. Use the documented
  complete command forms.
- Reports accept only `md`, `csv`, or `ant`; use `md` or `csv` for portable
  output. `ant` requires original PDFs/input paths and optional PDF support.
- The interactive shell is intentionally blocking. Use imports, validators, or
  bounded one-shot calls for automation.

## Runtime and safety

- Bound indexing (`maxsize`, `toprank`), querying (`topn`, `threshold`), report
  context, and RAG columns during development.
- Expect model downloads and large memory/disk use for dense or weighted indexes;
  capture logs and stop rather than repeatedly restarting a full corpus run.
- If a GPU is selected by the underlying model stack, verify device allocation
  with a tiny operation and retain the actual failure. paperai itself has no
  mandatory accelerator capability.
