---
name: local-farm-submission
description: "Guides Meshroom LocalFarm daemon, client, job/task, chunk
  expansion, and LocalFarmSubmitter submission workflows on Unix-like systems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Meshroom LocalFarm Submission

Use this route when a task mentions `meshroom_localfarm`, local farm roots, `LocalFarmSubmitter`, farm jobs/tasks, chunk expansion, or debugging a Meshroom submission without an external render farm.

## Read First

- [LocalFarm workflows](references/local-farm-workflows.md)
- [Submitter reference](references/submitter-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- Run [scripts/check_localfarm_imports.py](scripts/check_localfarm_imports.py) for a no-daemon import check.

## Platform Boundary

The local farm daemon currently relies on Unix process-fork behavior. Treat the daemon as Unix-only unless the implementation has changed. The client/task APIs can still be inspected on other platforms, but full daemon tests are not portable.

## Normal Flow

1. Choose a dedicated farm root for logs, PID/port state, and job files.
2. Start the daemon with `meshroom_localfarm --root ROOT start`.
3. Submit through `meshroom_batch --submit`, `meshroom_submit`, or `LocalFarmSubmitter`.
4. Inspect `status`/`fullinfo` and per-job task logs.
5. Stop or clean the farm after the job state is understood.

For general graph status or CLI flag selection route to [cli-pipeline-execution](../cli-pipeline-execution/SKILL.md). For generic plugin/submitter discovery route to [plugin-system](../plugin-system/SKILL.md).
