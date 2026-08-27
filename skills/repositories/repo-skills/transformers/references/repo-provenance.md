# Repo Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from the Hugging Face Transformers repository state below.

| Field | Value |
| --- | --- |
| Source repository | `huggingface/transformers` |
| Commit | `1048e9af78a6045444244412dfe216ba5810e7fb` |
| Branch | `main` |
| Exact tag | none detected |
| Package version | `5.13.0.dev0` |
| Dirty state at generation | dirty: generated `skills/` artifacts were untracked during skill creation |
| Remote URL | https://github.com/huggingface/transformers |

## Evidence Paths

Public runtime content was distilled from these repository-relative evidence paths:

- `README.md`
- `AGENTS.md`
- `pyproject.toml`
- `setup.py`
- `src/transformers/`
- `docs/source/en/`
- `examples/pytorch/`
- `examples/quantization/`
- `examples/modular-transformers/`
- `tests/cli/`
- `tests/generation/`
- `tests/trainer/`
- `tests/pipelines/`
- `tests/tokenization/`
- `tests/models/*/test_*token*`
- `tests/models/*/test_processing_*`
- `tests/quantization/`
- `tests/tensor_parallel/`
- `scripts/`
- `utils/`

## Excluded Evidence

The skill intentionally excluded or de-prioritized generated caches, translated duplicate docs, benchmarks, Docker/CI/release infrastructure, research-project examples, notebooks, and review/test artifact outputs unless they were useful for a public workflow summary.

## Refresh Guidance

Refresh this skill when any of these change materially:

- Major version, optional dependency groups, or CLI entry point behavior.
- `pipeline`, `GenerationConfig`, `TrainingArguments`, tokenizer/processor, serving, quantization, or modular model APIs.
- Contribution policy in `AGENTS.md` or model-copy/modular generation rules.
- Serving endpoints or continuous batching configuration.
- Example script layout or supported task recipes.
