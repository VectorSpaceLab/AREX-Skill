---
name: agents-workflows
description: "Guides DocsGPT agent types, prompts and sources, workflow graphs, shared state, CEL and templates, schedules, webhooks, seeding, and agent portability."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agents and Workflows

Use this sub-skill to choose/build an agent, design a workflow graph, automate it through schedules/webhooks, seed reusable agents, or export/import agent definitions.

## Route by task

- **Choose classic, agentic, research, or workflow**: read [agent types and lifecycle](references/agent-types-and-lifecycle.md).
- **Build/repair a node graph**: read [workflow design](references/workflow-design.md), then run the offline validator.
- **Schedule, webhook, seed, export/import**: read [schedules, webhooks, and portability](references/schedules-webhooks-portability.md).
- **Agent loops, missing state, invalid CEL, failed headless runs**: read [troubleshooting](references/troubleshooting.md).

## Agent type decision

| Type | Best fit | Retrieval style |
|---|---|---|
| `classic` | focused Q&A over known sources with predictable prefetch and optional tools | context retrieved before generation |
| `agentic` | model decides whether/how often to search and chain tools | internal search tool on demand |
| `research` | bounded multi-step clarification, planning, research and synthesis | adaptive search/tool phases with budgets |
| `workflow` | explicit deterministic graph, branches, shared state, files and code | configured per agent node |

Legacy `react` maps to classic behavior. Prefer current type names in new agents.

## Build an agent

1. Define task, users, expected evidence/output, and failure/approval policy.
2. Choose type and model based on tool/structured-output/attachment capabilities.
3. Add a system prompt with explicit scope and source-grounding rules.
4. Attach only necessary sources; choose chunks/retrieval exposure deliberately.
5. Enable only required tools and approvals.
6. Set research request/token/step/time budgets or workflow limits.
7. Test one success, one ambiguous input, one missing-evidence case, and one denied/failed tool.
8. Publish/share only after logs, citations, costs and authorization are correct.

## Workflow preflight

Export or author a workflow graph as JSON/YAML and run:

```bash
python scripts/validate_workflow.py workflow.json
```

The validator checks node ids/types, exactly one start, end reachability, edge references, condition else branches, `{{...}}` misuse in CEL fields, and obvious missing outputs. It does not execute code or call models.

Key syntax rule:

- AI prompt and End output templates use `{{variable_name}}`.
- Set State and Condition expressions use CEL bare identifiers such as `query` or `retry_count + 1`.

## Seed preflight

```bash
python scripts/validate_agent_seed.py agents.yaml
```

The helper validates agent names/types, prompt/source/tool shape and unresolved `${ENV_VAR}` placeholders without ingesting sources or writing Postgres. Actual seeding is stateful and requires a ready database/worker.

## Automation safety

- Webhooks and schedules are headless. Exclude tools that require a live user or could recursively create more schedules.
- Send `Idempotency-Key` on retryable webhook triggers.
- Bound schedule frequency, run time, count per user, failures and output retention.
- Treat webhook tokens as secrets.
- Poll task/run state to terminal completion and classify retryable versus permanent failures.

## Portability

Exported agent YAML strips secrets. Use the import plan endpoint before import; resolve/match sources, tools and prompts, then import as a draft and re-enter credentials. Workflow agents cannot be exported at this snapshot.

## Cross-skill routes

- Tool configuration and approval: [tools-integrations](../tools-integrations/SKILL.md)
- Source/retrieval behavior: [ingest-sources](../ingest-sources/SKILL.md) and [retrieval-vectorstores](../retrieval-vectorstores/SKILL.md)
- Native and OpenAI-compatible use: [api-client-operations](../api-client-operations/SKILL.md)
