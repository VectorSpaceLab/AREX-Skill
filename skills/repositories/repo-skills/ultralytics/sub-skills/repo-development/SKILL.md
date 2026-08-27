---
name: repo-development
description: "Use this sub-skill for maintainer-facing Ultralytics repository
  edits, editable installs, focused tests, docs/style checks, optional extras,
  CI-aware validation, and safe native verification planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Repo Development

Use this sub-skill when working inside the Ultralytics repository itself: editable setup, source edits, tests, docs/config updates, style tooling, optional development extras, CI-local parity, or safe native test selection.

## Route Elsewhere

- Dataset YAML authoring, config semantics, data paths, and augmentation configuration: `../data-and-configuration/SKILL.md`
- Training/validation commands, metrics, resume, devices, and dataset runtime behavior: `../training-and-validation/SKILL.md`
- Prediction, `Results` object usage, plotting, postprocessing, and CLI/Python inference: `../inference-and-results/SKILL.md`
- Export formats, deployment runtimes, benchmark mode, and backend installation: `../export-and-deployment/SKILL.md`
- Tracking mode and solution app operation: `../tracking-and-solutions/SKILL.md`
- Model family/task selection and architecture-level user guidance: `../model-families-and-tasks/SKILL.md`

Stay here when the user is editing repo code, tests, docs, packaging, CI, or maintainer tooling even if the touched subsystem is owned by another user-facing sub-skill.

## Fast Path

1. Confirm the checkout can import the editable package: `python -m pip install -e ".[dev]"` in a prepared development environment, then `python -c "import ultralytics; print(ultralytics.__version__)"`.
2. Classify changed paths before testing: `python sub-skills/repo-development/scripts/select_tests.py <changed-path> ...`.
3. Start with no-download checks (`yolo --help`, `yolo version`, `yolo cfg`, exact pytest nodes) before broad tests.
4. Add or update tests in the closest existing `tests/test_*.py` file unless the change introduces a new broad test category.
5. Use project-configured tools from `pyproject.toml`; do not invent a new formatter, linter, docs builder, or dependency policy.
6. Escalate from focused tests to full CI-like runs only when assets, optional extras, hardware, and network/cache policy are explicit.

## Common Commands

Editable maintainer setup:

```bash
python -m pip install -e ".[dev]"
python -c "import ultralytics; print(ultralytics.__version__)"
yolo --help
yolo cfg
```

Focused planner examples:

```bash
python sub-skills/repo-development/scripts/select_tests.py ultralytics/engine/results.py
python sub-skills/repo-development/scripts/select_tests.py --json docs/en/help/contributing.md mkdocs.yml
```

Cheap focused checks after parser/config changes:

```bash
pytest tests/test_cli.py::test_special_modes
pytest tests/test_python.py::test_cfg_init
yolo --help
yolo version
yolo cfg
```

Docs-only change planning should prefer markdown/style/reference checks and skip ML tests unless docs examples changed runtime code:

```bash
ruff check docs/en/help/contributing.md
python docs/build_reference.py
python docs/build_docs.py
```

Treat docs build scripts as environment-gated because they require docs/dev dependencies and may update generated files.

## Safe Native Test Selection

- `ultralytics/engine/results.py` changes should start with exact or file-level engine/API tests plus a direct `Results` smoke if needed; do not run export matrices unless exporter/backend code changed.
- `docs/`, `README.md`, and `mkdocs.yml` changes should route to markdown, Ruff, docs reference, and MkDocs checks; skip ML tests by default.
- `tests/` changes should run the changed test node/file first, then the adjacent subsystem only if the test exercises changed behavior.
- `ultralytics/cfg/default.yaml` and CLI parser changes should combine `tests/test_cli.py::test_special_modes`, `tests/test_python.py::test_cfg_init`, and `yolo cfg`.
- Export, CUDA, solutions, and integration tests are not default smoke checks; they require matching extras, hardware, cached assets, or explicit download permission.

## References

- Maintainer setup, style/config, optional extras, docs, CI, and PR guidance: `references/workflows.md`
- Changed-path test planner behavior and examples: `references/api-reference.md`
- Failure diagnosis for installs, CLI syntax, configs, downloads, devices, docs, and optional extras: `references/troubleshooting.md`
- Deterministic focused-test planner: `scripts/select_tests.py`
- Optional environment inspection helper: `scripts/check_ultralytics_env.py`
