# Repository Provenance

## Source Snapshot

- Skill id: `comfy-ui`
- Project: ComfyUI
- Package metadata name: `ComfyUI`
- Package metadata version: `0.25.0`
- VCS: git
- Branch: `master`
- Commit: `0d8b7510bdc5409f4a76c3191e122ddea50f4aa2`
- Exact tag: none detected
- Remote URL: https://github.com/comfyanonymous/ComfyUI
- Working tree state at generation: dirty because DisCo-created files were present under `skills/`

## Evidence Paths

Primary source and metadata evidence:

- `pyproject.toml`
- `requirements.txt`
- `README.md`
- `CONTRIBUTING.md`
- `QUANTIZATION.md`
- `main.py`
- `server.py`
- `execution.py`
- `nodes.py`
- `folder_paths.py`
- `comfy/`
- `comfy_execution/`
- `comfy_api/`
- `comfy_config/`
- `api_server/`
- `app/`
- `middleware/`
- `comfy_api_nodes/`
- `comfy_extras/`
- `custom_nodes/`
- `blueprints/`
- `models/configs/`
- `extra_model_paths.yaml.example`
- `script_examples/`
- `utils/extra_config.py`
- `tests/`
- `tests-unit/`
- `alembic_db/`

## Excluded Paths

Excluded from runtime skill extraction except where named as evidence above:

- `.git/`, caches, bytecode, build outputs, and temporary files
- model artifact directories under `models/` except `models/configs/`
- runtime user data/output directories such as `input/` and `output/`
- CI/release packaging internals not needed for user-facing workflows
- DisCo review/test artifacts under `skills/tests/`

## Inspection Notes

- Public runtime claims are based on repository source, package metadata, local tests/examples, and private package-inspection facts.
- Full ComfyUI execution can require optional model files, frontend/template packages, hosted API credentials, and hardware-specific torch/backend support.
- Future refresh checks should compare the commit, version, dirty-state summary, CLI flags, API routes, node API files, model path behavior, and bundled scripts against the current repository before reusing this skill unchanged.
