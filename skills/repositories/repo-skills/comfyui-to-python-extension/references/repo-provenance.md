# Repo Provenance

This file records the source state used to distill the ComfyUI-to-Python-Extension skill.

| Field | Value |
| --- | --- |
| Repository | ComfyUI-to-Python-Extension |
| Remote URL | https://github.com/pydn/ComfyUI-to-Python-Extension |
| Current commit | `6cdcc235a06c3354058d606fdd17daf7ca759190` |
| Branch | `main` |
| Exact tag | none |
| Working tree | clean |
| Package version | `2.1.0` |
| Python floor | `>=3.12` |

## Evidence paths

- `README.md`
- `pyproject.toml`
- `__init__.py`
- `comfyui_to_python/`
- `js/save-as-script.js`
- `tests/`
- `tests/runtime/run_runtime_validation.py`
- `tests/fixtures/runtime/`

## Notes

- The repository already contained a top-level `skills/` directory, so DisCo output was written under `skills/disco/` to avoid mixing generated runtime skill content with the pre-existing log artifact.
- The skill was distilled from the tracked source files listed above; it does not depend on any generated runtime outputs under `tests/runtime/generated/`.
