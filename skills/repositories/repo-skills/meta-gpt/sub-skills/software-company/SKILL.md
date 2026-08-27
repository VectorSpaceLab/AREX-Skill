---
name: software-company
description: "Use MetaGPT's core virtual software-company workflow from CLI or
  Python, including project generation, incremental updates, recovery, config
  initialization, and custom Role/Action/Team patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Software Company

Use this sub-skill when a user asks how to run MetaGPT as a virtual software company, generate a project from a one-line idea, continue an existing project, recover a serialized team, initialize configuration, choose CLI options, or build a small custom `Action`/`Role`/`Team` workflow.

## Quick Routing

| User intent | Use this sub-skill for | Key reference |
| --- | --- | --- |
| "Generate a 2048 game" or "build a repo from this idea" | `metagpt` CLI and `metagpt.software_company.generate_repo` project generation | [CLI and Python recipes](references/workflows.md#cli-project-generation) |
| "Explain MetaGPT CLI options" | Option names, defaults, boolean spelling, and safe dry checks | [CLI option guide](references/api-reference.md#cli-entry-point) |
| "Configure OpenAI/Claude/Ollama" | `config2.yaml` initialization, precedence, provider fields, and placeholder-key diagnosis | [Configuration workflow](references/workflows.md#configuration-workflow) |
| "Continue this project" | `--inc`, `--project-name`, `--project-path`, and QA rewrite inputs | [Incremental updates](references/workflows.md#incremental-project-updates) |
| "Recover a previous run" | `--recover-path` / `recover_path` validation and serialized `team` storage | [Recovery workflow](references/workflows.md#serialized-team-recovery) |
| "Build a custom agent/team" | Safe `Action`, `Role`, `RoleReactMode`, `Message`, and `Team` patterns | [Custom roles and teams](references/workflows.md#custom-action-role-and-team-patterns) |

## Before Running LLM Workflows

- Confirm Python is `>=3.9,<3.12`; Python 3.9 or 3.10 is the safest choice, and use the root MetaGPT installation/config guidance when present.
- Confirm `metagpt --help` works before any project-generation command.
- Initialize config with `metagpt --init-config`, then replace placeholder secrets in `~/.metagpt/config2.yaml`; do not paste API keys into chat or generated files.
- Treat `metagpt "Create a 2048 game"`, `generate_repo(...)`, `Team.run(...)`, debate examples, and custom roles that call `_aask(...)` as LLM-spending workflows requiring working provider config.
- Use `scripts/inspect_role_action.py --check-cli-help --json` for safe no-network inspection of installed APIs and CLI availability, then use root troubleshooting guidance for cross-cutting provider/config failures when present.

## Runtime References

- [Workflows](references/workflows.md): CLI/Python recipes, output layout, config, incremental/recovery usage, custom agent patterns, and safe validation.
- [API Reference](references/api-reference.md): important signatures, classes, parameters, defaults, and behavior notes.
- [Troubleshooting](references/troubleshooting.md): config placeholders, provider failures, dependency issues, Mermaid/browser problems, Typer/click help, `--inc`, `recover_path`, and long outputs.

## Boundaries

- For Data Interpreter roles, `DataAnalyst`/DI-generated project workflows, and notebook-style data analysis, route to the [`data-interpreter`](../data-interpreter/SKILL.md) sub-skill.
- For RAG, search, browser, tool registry, or retrieval internals, route to the [`rag-and-tools`](../rag-and-tools/SKILL.md) sub-skill.
- For AFlow, SPO, game examples beyond the core workflow, Android assistants, and environment extensions, route to `extensions-and-environments` when that sub-skill is present.
- For serialization internals, experiment pools, repository parser internals, and maintainer APIs, route to `maintainer-apis` when that sub-skill is present.
