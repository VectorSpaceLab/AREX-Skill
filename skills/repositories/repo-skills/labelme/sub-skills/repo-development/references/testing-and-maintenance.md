# Testing and Maintenance

## Environment and setup

This checkout uses uv in CI and declares Python 3.12, 3.13, and 3.14 support.
The normal development setup is:

```bash
make setup       # uv sync
make test        # pytest with the repo's default parallelism
make lint        # format, ruff, ty, TOML/Markdown/YAML checks, typos
```

Use a focused command first; reserve the full suite for integrated changes.

## Test map

| Changed area | Focused checks |
| --- | --- |
| `labelme/__main__.py` | `pytest tests/unit/__main___test.py -q`; CLI help/version |
| `labelme/_config/`, settings widgets | `pytest tests/unit/_config tests/unit/widgets/settings_dialog_test.py -q`; config e2e with display |
| `_label_file.py`, image codec | `pytest tests/unit/_label_file_test.py tests/unit/read_image_file_test.py -q` |
| `_shape.py`, shape utilities, canvas geometry | `pytest tests/unit/_shape_test.py tests/unit/utils/shape_test.py -q`; canvas tests for GUI paths |
| `_automation/` or AI widgets | `pytest tests/unit/_automation -q`; mocked AI e2e only when display exists |
| `examples/` converters | run a tiny disposable conversion; never write into tracked sample output |
| translations | `make check_translate` |
| release notes | `pytest tests/unit/tools/release_notes_test.py -q` |

## GUI and network gates

- GUI tests are marked `gui` and use pytest-qt/PySide6. On Linux CI the repo
  starts Xvfb and installs Qt platform libraries.
- Network tests are marked `network` and excluded by default. Real OSAM model
  downloads belong only in an explicitly selected network test.
- Do not use a CPU import or fake model session as proof of real model backend
  or inference quality; it only verifies control flow.

## Example safety

The CI example commands create generated output and then restore the checkout.
For local work, copy the input fixture or choose a disposable output directory.
Never make the runtime skill depend on original example paths; use the bundled
export helpers under the dataset-export sub-skill.

## Release and translation helpers

- `tools/release_notes.py` extracts release-note content and has a focused unit
  test; use it only for release maintenance.
- `tools/update_translate.py` updates translation sources/catalogs and can check
  whether they are current. It mutates generated translation files, so do not
  invoke it casually during a read-only investigation.
