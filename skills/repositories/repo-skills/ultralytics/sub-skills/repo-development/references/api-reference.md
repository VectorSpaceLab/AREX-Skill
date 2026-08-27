# Focused Test Planner Reference

Use `scripts/select_tests.py` to convert changed repository paths into focused maintainer checks without running tests or downloading assets.

## Usage

```bash
python sub-skills/repo-development/scripts/select_tests.py ultralytics/engine/results.py tests/test_engine.py
python sub-skills/repo-development/scripts/select_tests.py --json docs/en/help/contributing.md mkdocs.yml
```

The planner emits:

- Categories matched by changed paths.
- Pytest candidates ordered from narrow to broader checks.
- Safe CLI or docs commands to consider.
- Optional extras likely needed.
- Notes about network, cache, hardware, mutation, or sibling-routing risks.

## Path Routing Rules

| Changed path | Default focus | Avoid by default |
| --- | --- | --- |
| `ultralytics/engine/results.py` | `tests/test_engine.py`, `tests/test_python.py::test_model_methods`, optional direct `Results` smoke | export matrices and full media workflows |
| `ultralytics/engine/exporter.py` | export smoke and engine export tests | backend matrices without matching extras/runtimes |
| `ultralytics/cfg/default.yaml` or CLI parser/config | CLI special modes, config init, `yolo cfg` | training/validation matrices unless config behavior requires them |
| `ultralytics/data/` or dataset YAMLs | data utility/config validation tests | dataset downloads or training unless cache is prepared |
| `ultralytics/nn/` or `ultralytics/models/` | model construction/API smoke | broad task/model parametrization with uncached weights |
| `ultralytics/solutions/` | targeted solution tests with `solutions` extra awareness | similarity/video/Streamlit tests without assets/extras |
| `ultralytics/trackers/` or tracker YAMLs | tracker config and track-stream focused tests | online videos/ReID tests without download permission |
| `docs/`, `README.md`, `mkdocs.yml` | Ruff/docs/reference/MkDocs checks | ML tests unless examples changed runtime behavior |
| `.github/workflows/` | YAML review and local equivalents for edited commands | expecting exact GitHub Actions parity locally |
| `tests/` | changed exact node or file | full test suite before the changed test passes |

## JSON Output

`--json` produces a deterministic object with `categories`, `pytest`, `cli`, `extras`, and `notes`. Use it in automation or verification prompts when a downstream agent needs machine-readable focused checks.

## Safety Model

The planner is intentionally conservative. It suggests checks but never executes them, installs packages, downloads assets, touches datasets, writes docs output, or invokes export backends. Human or higher-level agent approval should decide when to run expensive checks.
