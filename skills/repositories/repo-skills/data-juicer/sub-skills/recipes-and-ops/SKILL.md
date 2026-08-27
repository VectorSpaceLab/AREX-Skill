---
name: recipes-and-ops
description: "Local Data-Juicer recipe processing, analysis, export, and utility workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# recipes-and-ops

Use this sub-skill for local Data-Juicer work that stays on one machine and does not depend on Ray recovery or the service/MCP surface.

## Start here
Read these references when the task is not trivial:
- `references/workflows.md`
- `references/configuration.md`
- `references/cli-reference.md`
- `references/troubleshooting.md`

## Owns
- `dj-process` local recipe execution
- `dj-analyze` dataset inspection
- dataset config, export config, validators, `text_keys`, and utility helpers
- operator discovery and safe dependency guidance for local recipes
- preprocess / postprocess / format conversion helpers

## Excludes
- Ray partitioning, resume, checkpointing, job monitoring, tracing -> `ray-and-recovery`
- FastAPI service, MCP server, operator search service -> `service-mcp`
- Spark launchers, maintainer-only pipelines, and heavy multimodal workflows unless they are only needed as troubleshooting notes

## Common flow
1. Inspect the recipe or dataset shape.
2. Choose local config, process list, and export target.
3. Run `dj-process` or `dj-analyze`.
4. If a dependency is missing, consult the troubleshooting reference before changing scope.

## Validation targets
- Can the user run a local recipe end to end?
- Are the dataset and export settings valid?
- Are failures explained with a concrete fix, not just a stack trace?

## When to route away
- Any mention of `executor_type: ray` or resume/checkpoint tokens
- Any mention of `dj-mcp`, FastAPI, or tool registration
- Any mention of cluster state, job lifecycle, or partition recovery
