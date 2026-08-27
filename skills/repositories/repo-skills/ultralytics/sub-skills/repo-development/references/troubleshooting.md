# Repo Development Troubleshooting

## Install Or Import Fails

Symptoms:

- `import ultralytics` imports an installed wheel instead of the edited checkout.
- `yolo` or `ultralytics` console scripts are missing.
- `pytest`, docs plugins, or optional backend packages are unavailable.

Actions:

- Reinstall from the repository root with `python -m pip install -e ".[dev]"`.
- Confirm import and console scripts with `python -c "import ultralytics; print(ultralytics.__version__)"`, `yolo --help`, and `ultralytics --help`.
- Install only the extra needed by the touched subsystem; avoid broad export/solutions stacks unless required.

## CLI Arg Syntax Is Wrong

Symptoms:

- CLI invocations fail because flags are written as `--imgsz 640` or positional values are misplaced.
- The command does not match Ultralytics `TASK MODE arg=value` shape.

Actions:

- Use `yolo TASK MODE arg=value`, for example `yolo detect predict model=yolo26n.pt source=image.jpg imgsz=640`.
- For repo smoke checks that avoid downloads, prefer `yolo --help`, `yolo version`, and `yolo cfg`.
- Route user-facing CLI usage questions to the relevant task sub-skill; keep this sub-skill focused on repo changes and tests.

## Bad Data Or Config Paths

Symptoms:

- A focused test starts downloading datasets unexpectedly.
- Dataset YAML, tracker YAML, or default config edits break path resolution.

Actions:

- Start with YAML/config parsing checks such as `pytest tests/test_python.py::test_cfg_init` and `yolo cfg`.
- Use tiny local temporary fixtures in tests instead of relying on remote datasets.
- Route dataset authoring and config semantics to `../data-and-configuration/SKILL.md` when the user is not editing maintainer code.

## Downloads Or Expensive Side Effects

Symptoms:

- Tests download weights, datasets, remote annotations, online media, or populate cache directories.
- Full test runs trigger training, export, video, or backend installation side effects.

Actions:

- Do not run `tests/cache_test_assets.py` unless asset predownload is explicitly allowed.
- Avoid full `pytest tests/`, `--slow`, CUDA tests, export matrices, online media, and solution similarity tests by default.
- Use exact test nodes, CLI help/config checks, and planner output first.
- State cache and network assumptions before proposing expensive commands.

## Backend Or Device Failures

Symptoms:

- CUDA tests skip or fail on CPU-only machines.
- TensorRT, CoreML, TensorFlow, OpenVINO, RKNN, QNN, Executorch, Axelera, or DEEPX tests fail due to platform/runtime/version constraints.

Actions:

- Treat clean CUDA skips as not applicable for ordinary CPU repo validation.
- Use `pytest tests/test_exports.py::test_export_env_has_smoke` before backend-heavy export tests.
- Install the matching export extra or use an isolated backend environment before running format-specific tests.
- Route deployment/runtime setup to `../export-and-deployment/SKILL.md`.

## Style, Docs, Or Docstring Failures

Symptoms:

- Ruff, pydocstyle, docformatter, import ordering, line length, or docs reference generation fails.
- Docs build scripts change generated Markdown/navigation/site files.

Actions:

- Follow Google-style docstrings and include type information in signatures or docstrings.
- Run configured tools from `pyproject.toml`; do not add new style config.
- Run docs build scripts only when docs/dev dependencies are installed and generated output can be reviewed.
- For docs-only changes, skip ML tests unless executable examples or source code behavior changed.

## Test Placement Review Feedback

Symptoms:

- A narrow change adds a new test file and maintainers ask for an existing file instead.

Actions:

- Put regression coverage in the closest existing file: `test_cli.py`, `test_engine.py`, `test_exports.py`, `test_integrations.py`, `test_python.py`, `test_solutions.py`, or `test_cuda.py`.
- Create a new test file only for a new broad category with maintainer agreement.
