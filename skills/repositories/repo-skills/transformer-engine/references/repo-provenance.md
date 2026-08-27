# Transformer Engine repo provenance

This file captures the source state used to generate the Transformer Engine repo skill.

| Field | Value |
| --- | --- |
| Repository | NVIDIA TransformerEngine |
| Source commit | `172bd93773ad6ee4ba44b460b7f10ef42fc89d57` |
| Branch | `main` |
| Exact tag | none |
| Working tree state | dirty: generated skill tree and review artifacts under `skills/` were added during creation |
| Package / version | `transformer_engine 2.19.0.dev0` |
| Remote URL | omitted-private-or-unknown |

## Evidence paths

All paths below are relative to the repository root.

- `README.rst`
- `pyproject.toml`
- `setup.py`
- `build_tools/VERSION.txt`
- `build_tools/utils.py`
- `build_tools/pytorch.py`
- `build_tools/jax.py`
- `docs/installation.rst`
- `docs/envvars.rst`
- `docs/faq.rst`
- `docs/api/common.rst`
- `docs/api/pytorch.rst`
- `docs/api/jax.rst`
- `docs/features/low_precision_training/introduction/introduction.rst`
- `docs/getting_started/getting_started_pytorch.py`
- `docs/getting_started/getting_started_jax.py`
- `tests/pytorch/test_sanity_import.py`
- `tests/jax/test_sanity_import.py`
- `examples/pytorch/fsdp/README.md`
- `examples/jax/encoder/README.md`
- `skills/tests/transformer-engine/reports/integration/repo_env_report.json`
- `skills/tests/transformer-engine/reports/integration/sub-skill-plan.md`

## Staleness note

This skill is aligned to the source state above. If the repo moves forward, regenerate or refresh the skill when the public APIs, install matrix, or source-build behavior change.
