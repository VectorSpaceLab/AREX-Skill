---
name: meta-gpt
description: "Use MetaGPT for multi-agent software-company workflows, Data
  Interpreter tasks, RAG/tools, extensions/environments, and repository
  maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MetaGPT

Use this repo skill when the user asks about MetaGPT, the `metagpt` Python package, the `metagpt` CLI, multi-agent software-company generation, Data Interpreter, RoleZero agents, MetaGPT RAG/tools, AFlow/SPO/extension environments, or maintaining MetaGPT internals.

## Start Here

1. Read [installation-and-configuration.md](references/installation-and-configuration.md) before running MetaGPT, changing providers, diagnosing config, or selecting optional dependencies.
2. Run [scripts/check_metagpt_environment.py](scripts/check_metagpt_environment.py) for safe import/config/CLI diagnostics that do not call an LLM or write a project.
3. Read [troubleshooting.md](references/troubleshooting.md) when imports, config validation, provider calls, optional dependencies, browser/Mermaid, or CLI commands fail.
4. Read [repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a MetaGPT checkout.

## Route By Task

| User task | Read |
| --- | --- |
| Generate a project from a one-line idea, use `metagpt` CLI options, initialize config, continue an existing project, recover a team, or build custom `Action`/`Role`/`Team` workflows | [software-company](sub-skills/software-company/SKILL.md) |
| Use Data Interpreter, RoleZero, DataAnalyst, SWEAgent, notebook/code execution, DI benchmark prompts, or tool-assisted data tasks | [data-interpreter](sub-skills/data-interpreter/SKILL.md) |
| Build or debug RAG pipelines, document stores, retrievers/rankers, search/browser/data/editor tools, tool registry, or optional RAG dependencies | [rag-and-tools](sub-skills/rag-and-tools/SKILL.md) |
| Use AFlow, SPO, Android Assistant, Stanford Town, werewolf/Minecraft/API environments, CR/SELA, or other extension integrations | [extensions-and-environments](sub-skills/extensions-and-environments/SKILL.md) |
| Maintain serialization, memory, experience pools, skill management, repo parsing, config models, focused tests, or public symbol inventories | [maintainer-apis](sub-skills/maintainer-apis/SKILL.md) |

## Install Baseline

MetaGPT is packaged as `metagpt==1.0.0` and declares Python `>=3.9,<3.12`. Prefer Python 3.9 or 3.10 for production-style use when following the project docs; Python 3.11 is useful for inspection but some dependencies can be slow or version-sensitive.

```bash
python -m pip install metagpt
# or, for a local checkout
python -m pip install -e .
metagpt --help
```

Before any workflow that calls an LLM, create or fix `~/.metagpt/config2.yaml` and replace placeholder API keys. `~/.metagpt/config2.yaml` has higher precedence than a checkout-local `config/config2.yaml`.

## Safe Validation

Use safe checks before expensive runs:

```bash
python scripts/check_metagpt_environment.py --json
metagpt --help
```

Do not use project generation, Data Interpreter, AFlow/SPO optimization, external environment simulations, browser automation, email automation, or RAG indexing as smoke tests unless the user has explicitly provided credentials, data, services, and cost approval.

## Capability Map

- **Software-company generation:** `metagpt "Create a 2048 game"`, `metagpt.software_company.generate_repo(...)`, incremental `--inc` mode, team recovery, custom roles/actions.
- **Data Interpreter:** planning, generated-code execution, data analysis, benchmark prompts, RoleZero-family roles, browser/OCR/email/Stable Diffusion examples behind explicit prerequisites.
- **RAG and tools:** document stores, retrievers/rankers, RAG factories, search providers, browser engines, tool registry/recommendation, optional dependency diagnostics.
- **Extensions/environments:** AFlow and SPO optimizers, Android Assistant, Stanford Town, werewolf, Minecraft/API/software environments, CR/SELA experiments.
- **Maintainer APIs:** serialization/deserialization, memory storage, experience pools, skill management, repo parser, config models, focused pytest selection.

## Common Decisions

- If a task is about using MetaGPT as a package or CLI, route to `software-company` unless Data Interpreter, RAG/tools, or extensions are named.
- If a task names a missing optional package, vector store, browser, Android device, dataset, or external service, route to the owning sub-skill and root troubleshooting before installing broad extras.
- If a task edits MetaGPT source code, route to `maintainer-apis` for focused tests and internals, then cross-link to the user-facing sub-skill that owns the affected workflow.
- If a run would call an LLM, spend tokens, send data to a provider, browse the web, reply to email, download datasets, or run a simulation, ask for explicit credentials/safety confirmation first.
