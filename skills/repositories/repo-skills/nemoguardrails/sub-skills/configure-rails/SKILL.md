---
name: configure-rails
description: "Create and validate NVIDIA NeMo Guardrails configs: config.yml,
  Colang flows, prompts, guardrail catalog rails, custom actions, providers,
  caching, knowledge base, and config migration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# configure-rails

Use this sub-skill when the task is about authoring or validating a guardrails configuration, not running chat, server, evaluation, or source-checkout work.

## Route here

- Create or repair `config.yml`, `prompts.yml`, `rails.co`/`main.co`, `config.py`, `actions.py`, `kb/`, `import_paths`, caching, or knowledge-base settings.
- Choose Colang 1.0 vs 2.x and load configs with `RailsConfig.from_path()` or `RailsConfig.from_content()`.
- Add built-in rails from the guardrail catalog or map a third-party rail to the right `models`/`rails` entries.
- Register custom actions, action parameters, providers, embedding providers, or embedding search providers.
- Migrate older Colang/config layouts with `nemoguardrails convert`.

## Route away

- Chat/server/runtime usage, streaming, RunnableRails, or `/v1/*` calls: `../run-rails/SKILL.md`.
- Evaluation, tracing, observability, or telemetry: `../evaluate-and-observe/SKILL.md`.
- Source checkout changes, PR policy, maintainer validation, or docs generation: `../repo-development/SKILL.md`.
- Install/import discovery only: `../setup-and-basics/SKILL.md`.

## Operating workflow

1. Start with `references/configuration-and-colang.md` to choose the right folder layout, loader, and Colang version.
2. Use `references/guardrail-catalog.md` to map the desired rail family to the required flow names, prompt tasks, model types, and optional dependencies.
3. Use `references/custom-actions-and-providers.md` for `actions.py`, `config.py`, provider registration, and embedding provider registration.
4. Use `references/troubleshooting.md` whenever config loading fails or a validation rule is expected to fire.
5. Validate with `scripts/validate_config.py`; pass `--instantiate` only when you want to confirm that `LLMRails` can be constructed without generating a response.

## Safe helper

```bash
python sub-skills/configure-rails/scripts/validate_config.py --config path/to/config
python sub-skills/configure-rails/scripts/validate_config.py --config path/to/config --instantiate
```

The helper loads the config, prints a concise summary, and never calls generation, chat, or server methods.
