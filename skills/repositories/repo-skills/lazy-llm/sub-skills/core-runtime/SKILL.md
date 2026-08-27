---
name: core-runtime
description: "Guides LazyLLM installation, optional extras, CLI commands,
  configuration, launcher, components, prompters, and base runtime diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LazyLLM Core Runtime

Use this sub-skill for base LazyLLM setup and runtime questions: package installation, optional extras, CLI command routing, `lazyllm.config`, namespace behavior, launchers, components/registries, prompters, dependency diagnostics, and safe source-checkout smoke tests.

## Start here when

- The user asks to install LazyLLM or choose between base, `rag`, `standard`, `full`, `dev`, or backend-specific extras.
- An import error names missing optional packages or `lazyllm install <extra>`.
- The task mentions `lazyllm` CLI commands: `install`, `deploy`, `run`, `skills`, `review`, or `review-local`.
- The task concerns `lazyllm.config`, environment-backed options, `lazyllm.namespace`, `ComponentBase`, component registration, prompt templates, or launcher/service scaffolding.
- You need a no-network check before moving to RAG, agents, models, writer, or flows.

## Files to read

- [config-cli-components.md](references/config-cli-components.md) for CLI command families, config behavior, prompters, components, and launcher notes.
- [troubleshooting.md](references/troubleshooting.md) for core install/import/CLI/config failure modes.
- Root [Installation and optional extras](../../references/installation-and-extras.md) for extra selection across workflows.
- [scripts/config_cli_smoke.py](scripts/config_cli_smoke.py) for a safe local smoke check of config, prompt, component registration, and CLI command table assumptions.

## Core workflow checklist

1. **Identify the selected workflow.** If the task is only config/CLI/import, keep it here. If it needs a domain feature, route onward after checking dependencies:
   - RAG/document import → [rag-document-processing](../rag-document-processing/SKILL.md)
   - Agents/tools/MCP → [agents-tools](../agents-tools/SKILL.md)
   - Model serving/provider/fine-tuning → [model-deployment](../model-deployment/SKILL.md)
   - Flow composition → [flow-orchestration](../flow-orchestration/SKILL.md)
   - Writer/review → [writer-review](../writer-review/SKILL.md)
2. **Check Python and install state.** LazyLLM 0.7.5 expects Python `>=3.10,<3.14`.
3. **Run a safe import/CLI diagnostic** when environment state is unclear:
   ```bash
   python ../../scripts/check_lazyllm_env.py --check-cli
   python scripts/config_cli_smoke.py
   ```
4. **Install the smallest extra** named by the failure. For example, RAG import failures usually require `lazyllm install rag`, not `full`.
5. **Avoid side effects.** Core runtime checks should not download models, call providers, start external services, or post reviews.

## CLI command families

The dispatcher recognizes these top-level commands:

```text
lazyllm install <extra1> <extra2> <pkg1> ...
lazyllm deploy modelname
lazyllm deploy mcp_server <command> [args ...] [options]
lazyllm run graph.json
lazyllm run chatbot
lazyllm run rag
lazyllm skills init/list/info/delete/add/import/install
lazyllm review ...
lazyllm review-local ...
```

A bare `lazyllm --help` can print usage and exit non-zero. Use concrete subcommands such as `lazyllm skills list` for smoke checks.

## Config and namespace facts

- `lazyllm.config` supports key lookup and mutation with option validation, aliases, default fallback for empty strings, and post-action hooks.
- Environment-backed values can be refreshed, and namespace contexts can redirect environment prefixes, for example `lazyllm.namespace("my")`.
- Tests verify `LAZYLLM_GPU_TYPE`, `LAZYLLM_DISPLAY`, alias normalization, strict options, and namespace isolation behavior.

## Component and prompt facts

- `lazyllm.components.register` can create groups and register callables/classes under lowercase and capitalization-preserving names.
- `fc_register` belongs to agents/tools, but simple tool registration metadata is often debugged from core runtime imports.
- `Prompter`, `AlpacaPrompter`, and `ChatPrompter` generate string prompts and OpenAI-style `messages` payloads with history support.

## Review before handing off

Before routing to a heavier sub-skill, leave the user with:

- active Python interpreter and LazyLLM version,
- selected optional extra or reason none is needed,
- safe command to reproduce the import/CLI/config state,
- explicit note if a provider, GPU, model download, external DB, parser service, MCP process, or remote review action is required.
