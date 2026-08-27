---
name: synthetic-data-generator
description: "Use SDGX/Synthetic Data Generator for tabular synthetic data,
  metadata inspection, relationship metadata, CLI fit/sample, LLM synthesis,
  evaluation metrics, and plugin-oriented extension workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Synthetic Data Generator (SDGX) Repo Skill

Use this skill when a task names `sdgx`, Synthetic Data Generator, or asks for structured/tabular synthetic data generation with SDGX APIs or the `sdgx` CLI. The package centers on `pandas` tables, metadata inspection, default data processors, CTGAN/GaussianCopula synthesis, OpenAI-backed tabular generation, and tabular quality metrics.

Do **not** use this skill for generic GAN theory, unrelated synthetic image/text generation, or privacy-policy decisions that are not about operating SDGX APIs.

## Fast orientation

- Public package/distribution: `sdgx`.
- Main import check: `import sdgx; print(sdgx.__version__)`.
- Main CLI: `sdgx` with `fit`, `sample`, and `list-*` subcommands.
- Primary high-level API: `sdgx.synthesizer.Synthesizer`.
- Canonical single-table ML model: `sdgx.models.ml.single_table.ctgan.CTGANSynthesizerModel`.
- Statistic model available by direct import: `sdgx.models.statistics.single_table.copula.GaussianCopulaSynthesizerModel`.
- LLM model: `sdgx.models.LLM.single_table.gpt.SingleTableGPTModel`.

Read [references/install-and-import.md](references/install-and-import.md) before installing, verifying imports, or choosing CPU/CUDA/OpenAI settings. Run [scripts/check_sdgx_environment.py](scripts/check_sdgx_environment.py) when you need a quick registry/import/backend check in the active environment.

## Quick install

```bash
pip install sdgx
python - <<'PY'
import sdgx
print(sdgx.__version__)
PY
sdgx --help
```

For local checkout work, `pip install .` or `pip install '.[test]'` from the repository root are the documented alternatives.

## Route by task

- **Data connectors, loaders, metadata, processors, cachers, inspectors, relationships, and plugins:** read [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md). Start here when the task is about CSV/DataFrame/generator inputs, metadata JSON, datetimes, fixed/specific column combinations, PII columns, caching, or custom extension registration.
- **Fit/sample tabular synthesizers or use the `sdgx` CLI:** read [sub-skills/single-table-synthesis/SKILL.md](sub-skills/single-table-synthesis/SKILL.md). Start here for `Synthesizer`, CTGAN, GaussianCopula, model save/load, `sdgx fit`, `sdgx sample`, `--json_output`, and `--torchrun`.
- **Generate tabular data with OpenAI-compatible LLMs or infer off-table features:** read [sub-skills/llm-synthesis/SKILL.md](sub-skills/llm-synthesis/SKILL.md). Start here for `SingleTableGPTModel`, `OPENAI_KEY`, `OPENAI_URL`, metadata-only generation, raw-data prompting, and response parsing.
- **Evaluate real vs synthetic data or adapt benchmark-style checks:** read [sub-skills/evaluation/SKILL.md](sub-skills/evaluation/SKILL.md). Start here for Jensen-Shannon divergence (`JSD`), mutual-information similarity (`MISim`), and safe metric scripts.

## Common operating pattern

1. Choose a data connector or create a `pandas.DataFrame`.
2. Build or inspect `Metadata` and optionally customize column types, primary keys, specific combinations, categorical encoders, and datetime formats.
3. Choose a model and entrypoint:
   - Library: `Synthesizer(model=..., data_connector=..., metadata=...)` then `fit()` and `sample(n)`.
   - CLI: `sdgx fit ...` then `sdgx sample ...`.
   - LLM: `SingleTableGPTModel` with raw data or metadata, after confirming key/base URL policy.
4. Validate outputs: expected columns, row count, null/datetime/PII behavior, and metric ranges.
5. Use troubleshooting references when imports, metadata checks, cache writes, optional dependencies, CUDA, or API credentials fail.

## Repo-level references

- [references/component-map.md](references/component-map.md) maps the SDGX architecture, managers, default processors, and public package surfaces.
- [references/install-and-import.md](references/install-and-import.md) records installation, import, environment variable, and backend guidance.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting failures shared by multiple workflows.
- [references/repo-provenance.md](references/repo-provenance.md) records the source version and evidence paths used to create this skill.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for `repo-skills-router` import.

## Guardrails

- Never assume the package has an installed inspection environment just because the checkout imports from the current directory; verify with the target Python.
- Do not run notebook or benchmark-scale workflows as quick checks. Use tiny fixtures and short smoke scripts unless the user explicitly requests benchmark execution.
- Treat LLM generation as a network/credential workflow. Do not send sensitive raw rows to an external API unless the user explicitly authorizes that data flow.
- When debugging an SDGX error, preserve the exact exception class from `sdgx.exceptions`; CLI `--json_output true` can surface structured exit messages.
