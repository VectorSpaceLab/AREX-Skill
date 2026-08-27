# Repo Provenance

Generated for the `unsloth` repository from a Git checkout.

## Source Snapshot

- Commit: `dbc13f02c989d6efc6c830796a4226c3f9a6cca6`
- Branch: `main`
- Exact tag: none detected
- Package distribution: `unsloth`
- Package version observed during inspection: `2026.6.8`
- Python requirement from package metadata: `>=3.9,<3.15`
- Remote URL: https://github.com/unslothai/unsloth

## Working Tree State

The source checkout was dirty because DisCo-generated runtime skill and review artifacts were being created under `skills/` during this run. No pre-existing repo-local skill was found before generation.

## Evidence Paths

Runtime skill content was distilled from these relative source paths:

- `pyproject.toml`
- `README.md`
- `unsloth/`
- `unsloth_cli/`
- `studio/backend/`
- `studio/install_llama_prebuilt.py`
- `studio/install_node_prebuilt.py`
- `studio/install_python_stack.py`
- `studio/setup.sh`
- `studio/setup.ps1`
- `install.sh`
- `install.ps1`
- `scripts/`
- `tests/`
- `unsloth_cli/tests/`
- `studio/backend/tests/`
- `tests/studio/`

## Refresh Signals

Refresh this skill when any of these change materially:

- `pyproject.toml` dependencies, optional extras, entry points, or Python range.
- Public loader/trainer/save APIs in `unsloth/`.
- CLI command signatures or option behavior in `unsloth_cli/`.
- Studio launch, auth, tool policy, provider, RAG, inference, llama.cpp, export, or setup behavior in `studio/backend/` or Studio setup scripts.
- Tests that define public behavior for CLI, Core loaders, saving/export, Studio runtime, hardware detection, or security constraints.
