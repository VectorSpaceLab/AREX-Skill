# Repository provenance

Schema: `disco.repo-provenance.v1`

This generated repo skill distills MAGI-1 source evidence into a self-contained operating graph for future DisCo Researcher sessions.

## Source snapshot

| Field | Value |
| --- | --- |
| Repository | SandAI-org/MAGI-1 |
| Remote URL | https://github.com/SandAI-org/MAGI-1.git |
| Commit | `0fcefdef8ce2df37a3b8890979433c06eb003328` |
| Branch | `main` |
| Exact tag | none detected |
| Package version | not declared in package metadata; repository has no `pyproject.toml`, `setup.py`, or `setup.cfg` in this checkout |
| License | Apache License 2.0 |
| Dirty state at skill generation | dirty because generated skill artifacts were written under `skills/`; source evidence files were otherwise read from the commit above |

## Evidence paths used

- `README.md`
- `requirements.txt`
- `LICENSE`
- `assets/prompt_enhancement_dify_dsl.yml`
- `example/4.5B/*.json`
- `example/4.5B/run.sh`
- `example/24B/*.json`
- `example/24B/run.sh`
- `example/assets/special_tokens.npz`
- `comfyui/README.md`
- `comfyui/README_CN.md`
- `comfyui/__init__.py`
- `comfyui/comfy_nodes.py`
- `comfyui/workflow/*.json`
- `inference/common/*.py`
- `inference/infra/checkpoint/*.py`
- `inference/infra/distributed/*.py`
- `inference/infra/parallelism/*.py`
- `inference/model/dit/*.py`
- `inference/model/t5/*.py`
- `inference/model/vae/*.py`
- `inference/pipeline/*.py`

## Evidence intentionally excluded

- `.git/` and local git metadata, except the public commit/branch snapshot above.
- `.codestyle/`, pre-commit configuration, and maintainer-only style hooks.
- `figures/` images, except their concepts already summarized by the README.
- Generated review/test artifacts under `skills/tests/`.
- Production logs such as `skills/*.log`.
- Any absent downloaded model weights or local cache directories.

## Refresh triggers

Refresh this skill if MAGI-1 changes any of the following:

- Inference CLI arguments in `inference/pipeline/entry.py`.
- `MagiPipeline` API signatures or generation modes.
- `MagiConfig`, `ModelConfig`, `RuntimeConfig`, or `EngineConfig` fields and validation rules.
- Example config families, checkpoint subdirectory semantics, or model zoo hardware notes.
- ComfyUI node class names, input/output sockets, workflow JSON shape, or plugin installation instructions.
- Dependency versions for PyTorch, CUDA, `flash-attn`, `flashinfer-python`, ffmpeg, or ComfyUI integration.
- Prompt enhancement DSL structure or provider requirements.
