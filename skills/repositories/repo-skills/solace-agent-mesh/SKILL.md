---
name: solace-agent-mesh
description: "Use Solace Agent Mesh to scaffold projects, configure agents and
  gateways, run tasks, author workflows, manage plugins, and evaluate agent
  systems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Solace Agent Mesh

Use this repo skill when a task mentions Solace Agent Mesh, SAM, the `sam` CLI, event-driven agent meshes, SAM projects, agents, gateways, proxies, workflows, plugins, task submission, Web UI/REST gateways, built-in tools, or `sam eval`.

Before doing live work, decide whether the user wants a **dry planning/validation task** or a **live runtime action**. Live actions can start brokers/gateways, call LLM providers, open browsers, write project files, install plugins, submit tasks, or run evaluations.

## First checks

- Package runtime: Python `>=3.10.16,<3.14`; public distribution `solace-agent-mesh`; CLI entry points `sam` and `solace-agent-mesh`.
- Install the main package in the active environment with `python -m pip install solace-agent-mesh` or, for a source checkout, build/install a normal local wheel instead of relying on editable CLI behavior.
- Optional REST client package: install `sam-rest-client` separately when you need `sam-rest-cli` or `SAMRestClient`. Treat it as a separate install surface when dependency pins conflict with the main package.
- For a safe import/CLI smoke check, run the bundled helper from this skill tree:

  ```bash
  python scripts/check_install.py
  python scripts/check_install.py --include-rest-client      # when both packages are intentionally installed together
  python scripts/check_install.py --rest-client-only        # when sam-rest-client is isolated
  ```

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.
- Use [references/package-overview.md](references/package-overview.md), [references/cli-reference.md](references/cli-reference.md), and [references/configuration-concepts.md](references/configuration-concepts.md) for shared context.
- Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/build/service issues.

## Route map

| User intent | Read this |
| --- | --- |
| Initialize a project, plan `sam init`, add agents/gateways/proxies, inspect generated layouts, or configure shared services | [sub-skills/project-bootstrap/SKILL.md](sub-skills/project-bootstrap/SKILL.md) |
| Create, install, catalog, add, inspect, or build SAM plugin packages | [sub-skills/plugin-lifecycle/SKILL.md](sub-skills/plugin-lifecycle/SKILL.md) |
| Start an existing SAM app, inspect built-in tools/docs, submit tasks, diagnose gateways, or use `sam-rest-client` | [sub-skills/runtime-operations/SKILL.md](sub-skills/runtime-operations/SKILL.md) |
| Author or validate workflow YAML/DAGs, node dependencies, map/switch/loop behavior, or template expressions | [sub-skills/workflow-authoring/SKILL.md](sub-skills/workflow-authoring/SKILL.md) |
| Configure `sam eval`, draft evaluation suites/test cases, validate files, or interpret result outputs | [sub-skills/evaluation/SKILL.md](sub-skills/evaluation/SKILL.md) |

## Operating boundaries

- Do not run `sam run`, `sam task`, `sam-rest-cli`, plugin installs/builds, catalog browsers, broker containers, LLM calls, or `sam eval` unless the user asked for live execution and the needed services/credentials are available.
- Do not rely on the original repository checkout for operating instructions. This skill's references and scripts are self-contained.
- If a task requires editing this repository rather than using SAM, treat that as repo maintenance and select normal coding-agent workflows; this skill is for operating the package.
- If package version, command names, public config schema, or evidence paths differ from [references/repo-provenance.md](references/repo-provenance.md), refresh the skill before relying on detailed instructions.
