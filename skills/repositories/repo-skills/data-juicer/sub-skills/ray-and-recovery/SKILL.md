---
name: ray-and-recovery
description: "Data-Juicer Ray execution, partitioning, checkpointing, recovery,
  and job lifecycle workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# ray-and-recovery

Use this sub-skill for Data-Juicer tasks that involve Ray execution, partitioned processing, checkpoints, resume semantics, job monitoring, or tracing.

## Start here
Read these references when the task is more than a smoke test:
- `references/workflows.md`
- `references/checkpointing.md`
- `references/job-management.md`
- `references/troubleshooting.md`

## Owns
- `executor_type: ray` and `executor_type: ray_partitioned`
- partition sizing, resume tokens, job IDs, event logs, checkpoint storage
- job snapshot, monitor, and stop helpers
- Ray analyzer, exporter, and tracer behavior
- safe local Ray availability checks

## Excludes
- Local recipe semantics without Ray -> `recipes-and-ops`
- FastAPI service and MCP routing -> `service-mcp`
- Spark launchers, cluster provisioning scripts, and maintainer-only distributed jobs unless they are only used as references

## Common flow
1. Verify Ray can start locally.
2. Choose a plain or partitioned executor.
3. Set work directory, checkpointing, and event logging deliberately.
4. Run the job, then inspect progress or recovery state with the job helpers.

## Validation targets
- Can the job resume after interruption?
- Are checkpoint and event-log paths stable?
- Are the failure messages specific enough to fix the configuration?

## When to route away
- Any mention of API routes, MCP transport, or operator search service
- Any mention of local-only dataset config tuning with no Ray execution
