---
name: pipelines
description: "Routes UltraRAG pipeline build, run, and recipe workflows,
  including YAML orchestration and the Python API wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipelines

Use this sub-skill when the task is about running, building, or authoring an
UltraRAG pipeline.

## Typical triggers

- `ultrarag build`, `ultrarag run`, or `ultrarag show`
- `ToolCall` / `PipelineCall` usage from Python
- `pipeline.yaml`, `servers:`, `pipeline:`, `loop:`, `branch:`
- Demo or experiment files under `examples/demos/` or `examples/experiments/`
- Questions about how a pipeline step consumes or produces variables
- Requests to reproduce or adapt a named example such as `RAG`, `LLM`,
  `LightResearch`, `AgentCPM-Report`, `webnote`, `search_o1`, `search_r1`,
  `rankcot`, `ircot`, `visrag`, or `sayhello`

## What this sub-skill covers

- CLI build/run/show entry points.
- `ToolCall` and `PipelineCall` from the Python API.
- Pipeline structure, variable resolution, step remapping, branch/loop logic,
  and generated `parameter/` and `server/` artifacts.
- Example workflows that combine benchmark data, retriever, generation, prompt,
  custom, memory, router, evaluation, and corpus steps.
- Safe smoke checks that prove the orchestration layer still works.

## What stays elsewhere

- Individual MCP server signatures and backend-specific configuration belong in
  `sub-skills/servers/`.
- Flask UI, chat sessions, knowledge-base storage, and case study belong in
  `sub-skills/ui-and-storage/`.

## Start here

- Read `references/pipeline-dsl.md` for the verified YAML syntax, data-flow
  rules, and build/run behavior.
- Read `references/workflows.md` for a map of example families and the best
  starting point for each one.
- Read `references/troubleshooting.md` when a pipeline build, parameter merge,
  or execution step fails.
- Run `scripts/smoke_sayhello_pipeline.py` for a minimal end-to-end smoke check.

## Common user questions this sub-skill should answer

- How do I build a pipeline from YAML?
- How do I run a pipeline with a custom parameter file?
- How do I express a loop or branch?
- Why did a step remap or variable lookup fail?
- Which example pipeline is closest to my task?
- How do I get a small smoke test working before a larger RAG workflow?

## Practical workflow

1. Identify the example family that matches the request.
2. Check whether the task is only orchestration, or whether it also needs a
   specific server backend or UI route.
3. Use the DSL reference to confirm the step shape and variable names.
4. Use the smoke script or a minimal example to validate the plan.

## Helpful commands

Use the bundled smoke helper instead of relying on a source example file:

```bash
python sub-skills/pipelines/scripts/smoke_sayhello_pipeline.py --repo-root <checkout>
ultrarag show ui
ultrarag show case --config_path <memory-case.json>
```

If the task is about a named experiment or demo, use the distilled family map in
`references/workflows.md` before guessing the pipeline structure.
