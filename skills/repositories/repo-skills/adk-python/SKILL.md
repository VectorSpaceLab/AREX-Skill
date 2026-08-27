---
name: adk-python
description: "Use Google ADK Python to build agents, Workflow graphs, tools,
  runtime services, CLI apps, evaluations, deployments, and ADK repository
  changes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ADK Python

Use this repo skill when a task involves Google Agent Development Kit for Python (`google-adk` / `google.adk`), ADK 2.0 `Agent` and `Workflow` APIs, ADK CLI commands, tool integrations, runtime services, evaluation/debugging, or modifying the ADK Python repository itself.

## Start Here

- Install the package with `pip install google-adk` on Python 3.10+.
- For optional integrations, install the narrow extra for the task instead of `all` by default, such as `google-adk[db]`, `google-adk[mcp]`, `google-adk[eval]`, `google-adk[gcp]`, or `google-adk[extensions]`.
- Verify the base install with `python -c "import google.adk; print(google.adk.__version__)"` and `adk --help`.
- Run [check_adk_install.py](scripts/check_adk_install.py) for a safe diagnostic covering imports, CLI command availability, package version, and optional-extra signals.
- Read [Repository Provenance](references/repo-provenance.md) before deciding whether this skill is current for a checkout; refresh if commit, dirty state, package version, or major evidence paths changed.

## Route by Task

- **Build Python agents:** Use [agent-construction](sub-skills/agent-construction/SKILL.md) for `Agent`/`LlmAgent`, instructions, model settings, callbacks, schemas, task/single-turn modes, sub-agents, and multi-agent delegation.
- **Build Workflow graphs:** Use [workflow-orchestration](sub-skills/workflow-orchestration/SKILL.md) for `Workflow`, `BaseNode`, function nodes, graph edges, `JoinNode`, dynamic nodes, parallel worker, HITL, retry, checkpoint/resume, and event flow.
- **Add tools or integrations:** Use [tools-and-integrations](sub-skills/tools-and-integrations/SKILL.md) for `FunctionTool`, `ToolContext`, toolsets, confirmation/long-running tools, auth, MCP, OpenAPI, Google API/cloud integrations, A2A, and optional extras.
- **Configure runtime services:** Use [runtime-services](sub-skills/runtime-services/SKILL.md) for `Runner`, `App`, sessions, memory, artifacts, plugins, telemetry, code executors, environments, event persistence, and service lifecycles.
- **Use CLI/config/deployment:** Use [cli-configuration-deployment](sub-skills/cli-configuration-deployment/SKILL.md) for `adk run`, `adk web`, `adk api_server`, `adk test`, `adk eval`, `adk deploy`, app discovery, YAML config, service URIs, and safe CLI/schema inspection.
- **Evaluate or debug behavior:** Use [evaluation-debugging](sub-skills/evaluation-debugging/SKILL.md) for eval sets, JSON test fixtures, `adk test`, `adk eval`, event summaries, traces, session inspection, flaky evals, and assertion design.
- **Modify this repository:** Use [repo-development](sub-skills/repo-development/SKILL.md) for ADK Python source edits, style, tests, docs, samples, generated schema, review gates, and repository-specific validation.

## Shared References

- [Capability Map](references/capability-map.md) maps common user request families to sub-skills, bundled scripts, and validation expectations.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting install/import, optional dependency, CLI, credential, server, and repository-staleness failures.
- [Repository Routing Metadata](references/repo-routing-metadata.json) is structured metadata used by DisCo's managed `repo-skills-router` during import.

## Safe Defaults

- Prefer import/signature checks, `--help`, and dry-run diagnostics before starting servers, deployments, cloud calls, model-backed evals, or database migrations.
- Do not assume optional extras are installed in base `google-adk`; diagnose missing modules and install only what the selected workflow requires.
- Do not put API keys, OAuth secrets, service-account JSON, production database URLs, or cloud project credentials into examples or YAML files.
- For repository-maintenance tasks, run focused tests first and avoid remote/cloud/credentialed tests unless the user explicitly asks and the environment is configured.

## Minimal Examples

Create a simple agent:

```python
from google.adk import Agent

root_agent = Agent(
    name="greeter",
    model="gemini-2.5-flash",
    instruction="Greet the user and answer briefly.",
)
```

Create a simple workflow:

```python
from google.adk import Workflow

root_agent = Workflow(
    name="fruit_flow",
    edges=[("START", pick_fruit, explain_benefit)],
)
```

Run local checks:

```bash
python scripts/check_adk_install.py --json
adk --help
adk run path/to/my_agent --help
```
