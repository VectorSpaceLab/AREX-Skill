---
name: "generic-conversion"
description: "Explains the reusable BaseAdapter and ConversionTask contract and
  the safe local or Ray generic LeRobot conversion pipeline when a user is
  designing, validating, or troubleshooting a dataset adapter."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generic conversion

Use this route when a source-specific adapter already knows how to discover raw
inputs and yield LeRobot-compatible episodes, but needs the shared task
orchestration, temporary datasets, aggregation, cleanup, resume, or Hub
boundary. It is an operating contract, not a source-dataset converter.

## Route boundary

- Use `BaseAdapter` and `ConversionTask` for a new or existing adapter whose
  inputs can be represented as independent conversion tasks.
- Route source layouts, encodings, and filtering to the owning sibling route:
  `openx-conversion`, `agibot-conversion`, `robomind-conversion`,
  `libero-conversion`, or `robocasa-conversion`.
- Route LeRobot-to-RLDS work to `rlds-export` and LeRobot format changes to
  `version-migration`. Do not use this route to infer historical metadata
  layouts or to regenerate simulator data.
- The runtime skill does not import a source checkout, run a conversion,
  download data, start Ray, render a simulator, or push to the Hub while
  planning or validating an adapter.

## Operating procedure

1. **Confirm the environment.** Check that the selected LeRobot API exposes the
   dataset creation, aggregation, and video helpers expected by the adapter.
   Import `datatrove` even for local execution because the shared pipeline
   imports it. Treat Ray, video codecs, and Hub credentials as optional gates,
   not assumptions. See [troubleshooting](references/troubleshooting.md).
2. **Define the adapter contract.** Set `dataset_type`, positive `fps`,
   `robot_type`, and a complete `features` mapping; add stable `tags` only when
   useful. Implement `load_tasks()` and `load_subset(task)`. Keep raw-source
   details in `task.metadata`, not in generic pipeline logic.
3. **Make frames unambiguous.** Each yielded episode should be a materialized
   sequence of frame dictionaries accepted by the target LeRobot writer. Put a
   `task` field in every frame when language/task conditioning is intended.
   Validate array shapes, dtypes, image/video keys, and episode lengths before
   scheduling expensive work.
4. **Plan paths.** Give every task a unique temporary `output_path`, normally
   below the adapter's sibling `<final-name>_temp` path. Keep the final output
   separate from all raw inputs and unrelated existing datasets. The pipeline
   deletes existing task outputs and deletes an existing final output before
   aggregation; inspect the plan before running.
5. **Start locally.** Call `run_converter(..., executor="local", ...)` for a
   first smoke test. `workers=-1` derives workers from CPU count and
   `cpus_per_task`; an explicit small worker count is safer for video and
   memory-heavy adapters. `tasks_per_job` affects the Ray configuration, not
   local scheduling.
6. **Use Ray deliberately.** Select `executor="ray"` only after the Ray/DataTrove
   extras, worker visibility, shared paths, and memory budget are proven. The
   route initializes Ray and passes a small runtime environment; it does not
   prove a cluster is reachable or make source files available on every node.
7. **Use debug before scale.** `debug=True` overrides the request to local
   execution, uses one worker, truncates the task list to its first two tasks,
   and disables Hub pushing. It still validates the original task list and CPU
   count first. Treat this as a bounded smoke test, not a representative run.
8. **Review the aggregate.** Confirm that temporary roots existed, the final
   dataset metadata and indices agree, normalized arrays remain readable, and
   video references/timestamps are valid. Keep temporary outputs with
   `cleanup_temp=False` only for deliberate inspection; remove them after the
   review.
9. **Push only after local review.** `push_to_hub=True` requires a distinct
   `hub_repo_id`. It uploads videos, uses public visibility, and applies the
   deduplicated LeRobot/dataset/robot/adapter tags. Authenticate and confirm
   destination ownership separately; do not use a Hub id as permission to
   overwrite an unrelated local path.

## Contract and pipeline details

Use the exact field and hook behavior in [the API reference](references/api-reference.md),
the execution and aggregation model in [pipeline behavior](references/pipeline-behavior.md),
and the failure matrix in [troubleshooting](references/troubleshooting.md).
The optional [safe contract checker](scripts/check_generic_contract.py) checks a
JSON adapter manifest without importing an adapter or writing a dataset.

## Minimal preflight

Before a real run, record: the source-specific route and evidence, target
LeRobot version, final output path, task count and unique temporary roots,
feature schema, task metadata policy, executor, CPU/memory budget, resume-log
identity, cleanup decision, and Hub destination. For a multi-task adapter using
an existing resume directory, verify that the log belongs to the same task
manifest and paths. Never let a resume convenience authorize deletion of an
unrelated final output.

A zero-task manifest and `cpus_per_task < 1` are hard preflight errors. The
checker and the pipeline intentionally expose these cases rather than
silently producing an empty dataset. No native conversion is implied by this
skill; only safe static or synthetic contract checks belong here.

## Evidence and staleness

This route distills the repository's `generic_converter` README, adapter,
utility, and pipeline modules, plus the root, AgiBot, and LIBERO README
descriptions. Those artifacts establish behavior but are not runtime
 dependencies. If the installed LeRobot package changes its import locations,
writer signatures, aggregation schema, or video format, revalidate this route
and the source-specific sibling route before use.
