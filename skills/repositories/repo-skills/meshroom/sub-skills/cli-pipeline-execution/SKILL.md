---
name: cli-pipeline-execution
description: "Guides Meshroom batch, compute, inspect, status, statistics,
  submit, scene-generation, and scene-parameter CLI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Meshroom CLI and Pipeline Execution

Use this route for command-line scene creation, local computation, output-node configuration, graph status/statistics inspection, parameter extraction, or CLI submission.

## Read First

- [CLI reference](references/cli-reference.md)
- [Pipeline workflows](references/pipeline-workflows.md)
- [Scene parameter helpers](references/scene-parameter-helpers.md)
- [Troubleshooting](references/troubleshooting.md)
- Run the root [runtime checker](../../scripts/check_meshroom_runtime.py) with `--repo-root` and `--cli-help` for safe parser checks.

## Command Selection

| Need | Command |
| --- | --- |
| Create/configure a graph from a template or `.mg` file | `meshroom_batch` |
| Compute an existing `.mg` graph | `meshroom_compute` |
| Print version, node info, or template info | `meshroom_info` |
| Submit a saved graph through a submitter | `meshroom_submit` |
| Query node/chunk statuses | `meshroom_status` |
| Query resource/time statistics and optional HTML export | `meshroom_statistics` |
| Create farm chunk tasks or execute chunks | `meshroom_createChunks` |
| Generate a descriptor skeleton from external `--help` output | `meshroom_newNodeType` |
| Start/query the built-in Unix local farm | `meshroom_localfarm` |

## Safe Operating Loop

1. Run `meshroom_info version` and `meshroom_info pipelines` to confirm the runtime/template paths.
2. Use `meshroom_batch --compute no --save scene.mg` to validate a configured scene before running external binaries.
3. Inspect graph status with `meshroom_status scene.mg`.
4. Compute locally with `meshroom_compute scene.mg` or submit with `meshroom_submit scene.mg --submitter NAME`.
5. Use `meshroom_status --node NODE` and `meshroom_statistics --node NODE` to isolate failures.
6. Preserve the `.mg` file and cache/status logs when reporting a failure.

Route graph compatibility or programmatic graph mutation to [core-graph-engine](../core-graph-engine/SKILL.md), and LocalFarm daemon/task behavior to [local-farm-submission](../local-farm-submission/SKILL.md).
