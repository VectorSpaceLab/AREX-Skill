---
name: extensions-and-environments
description: "Use MetaGPT extension optimizers, Android/Stanford
  Town/werewolf/Minecraft integrations, and external environment APIs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Extensions and Environments

Use this sub-skill when a request involves MetaGPT extension workflows or external environment integrations: AFlow workflow optimization, SPO prompt optimization, CR code-review experiments, SELA AutoML experiments, Android Assistant, Stanford Town, werewolf, Minecraft, MGX/software environments, or custom `ExtEnv` read/write APIs.

## Route Here For

- Running safe preflight for AFlow or SPO optimizer entrypoints without downloading datasets or calling LLMs.
- Planning AFlow optimization, custom AFlow benchmarks, workflow templates, operators, datasets, and optimizer output directories.
- Planning SPO prompt optimization, template YAMLs, CLI/API use, Streamlit UI setup, and prompt output inspection.
- Understanding Android Assistant learning/acting stages, ADB/device/emulator prerequisites, screenshots/XML paths, and safe setup checks.
- Starting or adapting Stanford Town or werewolf simulations when the user confirms LLM cost, assets, services, and run length.
- Designing custom environment integrations with `ExtEnv`, `Environment`, `EnvAPIAbstract`, `mark_as_readable`, `mark_as_writeable`, and concrete Android/Stanford Town/werewolf/Minecraft envs.
- Understanding high-level CR and SELA extension flows, including Python/Java patch review points and AutoML/MCTS experiment configs.

## Route Elsewhere

- Core `Action`, `Role`, `Team`, CLI project generation, incremental runs, and software-company workflows: use `software-company`.
- Data Interpreter task planning/execution and notebook-style analysis: use `data-interpreter`.
- RAG pipelines, search/browser tools, vector stores, and tool registries: use `rag-and-tools`.
- Serialization, maintainer internals, memory/experience persistence APIs, and repository parser internals: use `maintainer-apis` when present.
- Provider credentials, root installation, and cross-cutting LLM configuration failures: use the root MetaGPT config/troubleshooting guidance first, then return here for extension-specific setup.

## Reference Map

- `references/workflows.md`: AFlow, SPO, Android Assistant, Stanford Town, werewolf, CR/SELA, Minecraft, and custom environment recipes.
- `references/api-reference.md`: extension modules, optimizer classes, environment APIs, action/observation spaces, and config concepts.
- `references/configuration.md`: optimizer configs, LLM model names, datasets, workspaces, device/browser/service prerequisites, and skip conditions.
- `references/troubleshooting.md`: missing datasets/templates, API keys, long optimization costs, optional imports, Android/ADB, simulations, Minecraft services, and environment API misuse.
- `scripts/optimizer_help_check.py`: safe helper for AFlow/SPO parser help and module import availability checks.

## Safe First Steps

1. Use `scripts/optimizer_help_check.py --target all --mode help` to confirm bundled AFlow/SPO parser surfaces without importing optimizer modules or running optimization.
2. Treat AFlow/SPO full optimization, CR confirmation, SELA experiments, Android Assistant, Stanford Town, werewolf, and Minecraft as LLM-costing, service/device-dependent, or long-running unless the user explicitly confirms prerequisites.
3. Prefer planning, config validation, parser help, and module import checks before any command that downloads datasets, starts devices/services, launches browser/UI processes, or runs multi-round simulations.
