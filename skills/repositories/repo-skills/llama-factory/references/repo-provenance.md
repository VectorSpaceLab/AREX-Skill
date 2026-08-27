# Repo Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- Repository: LlamaFactory / LLaMA-Factory
- Package distribution: `llamafactory`
- Package version: `0.9.6.dev0`
- Commit: `8792f06161c2e0240a9762eab61e41cfb3ea5580`
- Branch: `main`
- Exact tag: none detected
- Remote URL: `https://github.com/hiyouga/LlamaFactory.git`
- Working tree state during generation: dirty because new `skills/` files were created for this DisCo run

## Decision Policy

- Extraction scope: agent-confirmed from user request `auto decide`
- Import policy: `auto import` only after successful verification
- Inspection environment: partial only; dependency-complete install timed out during large ML wheel downloads, so runtime claims are based on source, docs, examples, tests, and lightweight package metadata/import checks

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `src/llamafactory/`
- `src/llamafactory/v1/`
- `docs/en/`
- `examples/`
- `data/`
- `requirements/`
- `scripts/`
- `tests/`
- `tests_v1/`
- `Makefile`
- `CLAUDE.md`

## Refresh Triggers

Refresh this skill when any of these change materially:

- CLI routes or launcher behavior in `src/llamafactory/cli.py` or `src/llamafactory/launcher.py`
- Training/data/model/inference hparams or dataclass validation
- Dataset registry schema, template registry, multimodal plugins, or processors
- Model loading/export, quantization, adapter merge, or optional backend requirements
- v1 launcher/config/core/trainer/plugin behavior
- Public examples, docs, or tests that define user workflows
