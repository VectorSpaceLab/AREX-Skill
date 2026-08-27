# Repo Development Workflows

## Editable Setup

Use an editable install for repository work so source edits are imported immediately:

```bash
python -m pip install -e ".[dev]"
python -c "import ultralytics; print(ultralytics.__version__)"
yolo --help
```

The `dev` extra contains maintainer basics such as `pytest`, `pytest-cov`, `pytest-xdist`, coverage tooling, and docs support packages. Install narrower extras only when the touched area requires them:

- `export-base` for ONNX/OpenVINO/NNCF/ONNX Runtime style export smoke tests.
- `export-tensorflow`, `export-coreml`, `export-executorch`, or `export-deepx` for backend-specific export work.
- `export` for broad export stacks when a disposable environment can tolerate heavy dependencies.
- `solutions` for Shapely, LAP, FAISS, CLIP, Streamlit, and Flask solution coverage.
- `logging` for W&B, TensorBoard, or MLflow integration work.
- `extra` for notebook, augmentation, and COCO evaluation helpers.
- `typing` for type-stub-assisted maintainer checks.

Avoid installing heavyweight extras to validate a narrow parser, docs, or utility change.

## Style And Config

`pyproject.toml` is the source of truth for local tool settings:

- Pytest uses doctest modules, duration reporting, a `slow` marker, and skips recursion into build/dist/git directories.
- Ruff uses a 120-column line length, Google pydocstyle convention, and docstring code formatting.
- YAPF uses PEP 8 base style with 120 columns and project-specific splitting/spacing.
- isort uses 120 columns and single-line multi-line output mode.
- docformatter wraps summaries and descriptions to 120 columns and edits files in place.
- codespell skips model weights, binary exports, media, cache/run directories, generated docs translations, and known project terms.

Use existing repo configuration rather than adding a new formatter or linter config.

## Tests And CI Local Parity

Start narrow, then broaden:

1. Run `python sub-skills/repo-development/scripts/select_tests.py <paths>`.
2. Run exact pytest nodes or a single test file.
3. Add adjacent subsystem tests when behavior spans files.
4. Run full `pytest tests/ --export-env base` only in an environment prepared for repository CI behavior.

Common safe checks:

```bash
pytest tests/test_cli.py::test_special_modes
pytest tests/test_python.py::test_cfg_init
pytest tests/test_exports.py::test_export_env_has_smoke
yolo --help
yolo version
yolo cfg
```

CI workflows run broader combinations such as coverage, xdist, slow tests, CUDA tests, export environment matrices, Docker checks, link checking, docs builds, and package smoke tests. Treat those as CI-parity targets, not default local validation.

## Docs Changes

Docs sources live under `docs/` with site configuration in `mkdocs.yml`. Docs CI installs the development extra and Ruff, checks selected docs/source paths, runs reference generation, validates generated reference docs, and runs the docs builder.

Use this escalation:

```bash
ruff check <touched-doc-or-source-files>
python docs/build_reference.py
python docs/build_docs.py
```

Run docs build scripts only in a docs-prepared environment because they require docs dependencies and can mutate generated reference or site output.

## Contributor And PR Expectations

- Keep first-time or speculative PRs small and focused.
- Include tests for behavior changes and docs updates for user-facing changes.
- Prefer adding coverage to an existing `tests/test_*.py` file close to the changed subsystem.
- Use Google-style docstrings for new public functions/classes; simple helpers can use complete one-line docstrings.
- Preserve AGPL-3.0 and CLA language; route legal conclusions to qualified counsel rather than giving legal advice.
