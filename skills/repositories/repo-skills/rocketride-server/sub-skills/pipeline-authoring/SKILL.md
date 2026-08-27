---
name: pipeline-authoring
description: "Author, validate, debug, and adapt RocketRide .pipe workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Pipeline Authoring

Use this sub-skill when you need to create or revise a RocketRide `.pipe` workflow,
reason about data-lane versus control/invoke wiring, or prepare a workflow for
static validation before an engine run.

## Use this for

- New `.pipe` workflows or edits to existing ones
- Repairing lane wiring, source/target placement, or control connections
- Replacing hardcoded credentials with environment placeholders
- Adapting RAG, document-processing, multi-agent, or n8n round-trip patterns
- Checking a workflow before handing it to the engine or IDE

## Do not use for

- SDK method details, client usage, or CLI commands → `../sdk-clients/SKILL.md`
- Provider catalog, node READMEs, or schema depth → `../nodes-catalog/SKILL.md`
- Server startup, deployment, or runtime operations → `../runtime-deployment/SKILL.md`
- Deeper MCP or n8n integration behavior → `../mcp-and-integrations/SKILL.md`

## Working order

1. Read the current pipeline shape and identify the source, targets, and any
   nested sub-pipelines.
2. Separate data lanes from control/invoke connections.
3. Replace secrets with `${ROCKETRIDE_*}` placeholders.
4. Keep `project_id`, `source`, `viewport`, and `version` aligned with the file's
   actual entry point and canvas state.
5. Run static validation before any engine run.

## Validation helper

Use the shared static probe `../../scripts/rocketride_static_probe.py` to check
JSON shape, references, lane wiring, and control ownership before execution.

## Reference map

- [Schema and recipes](references/pipeline-schema-and-recipes.md)
- [Troubleshooting](references/troubleshooting.md)

## What good output looks like

- Unique component ids
- One explicit entry source
- Correct lane types end to end
- Control connections on the controlled node
- No hardcoded secrets
- Safe, engine-ready JSON
