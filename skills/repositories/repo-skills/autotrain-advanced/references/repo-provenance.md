# Repo provenance

This generated skill was distilled from the AutoTrain Advanced repository state below.

| Field | Value |
| --- | --- |
| schema | `disco.repo-provenance.v1` |
| source_repo | Hugging Face `autotrain-advanced` |
| remote_url | https://github.com/huggingface/autotrain-advanced |
| vcs | git |
| commit | `1873aca349c88684e83c8fd3d79a1c638cfbe636` |
| branch | `main` |
| tag | none |
| working_tree | clean |
| package_version | `0.8.37.dev0` |
| install_verification | editable install and CLI/import checks completed in a private inspection environment |

## Evidence paths

All paths below are relative to the repository root.

- `README.md`
- `docs/README.md`
- `setup.py`
- `setup.cfg`
- `requirements.txt`
- `src/autotrain/__init__.py`
- `src/autotrain/cli/autotrain.py`
- `src/autotrain/cli/*.py`
- `src/autotrain/app/*.py`
- `src/autotrain/backends/*.py`
- `src/autotrain/trainers/*/params.py`
- `src/autotrain/preprocessor/*.py`
- `src/autotrain/tools/*.py`
- `configs/**`
- `colabs/*.ipynb`
- `notebooks/*.ipynb`

## Notes

- The repository is public, but the generated skill should remain self-contained and not depend on the source checkout at runtime.
- `autotrain vlm` is not a registered top-level CLI command in the inspected checkout; VLM support is surfaced through the app/API/config path instead.
