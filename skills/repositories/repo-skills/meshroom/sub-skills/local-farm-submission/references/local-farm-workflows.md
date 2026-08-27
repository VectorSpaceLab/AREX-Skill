# LocalFarm Workflows

## Daemon Lifecycle

```bash
meshroom_localfarm --root /work/local-farm start
meshroom_localfarm --root /work/local-farm status
meshroom_localfarm --root /work/local-farm fullinfo
meshroom_localfarm --root /work/local-farm stop
```

The farm root contains the backend log, PID/port state, and per-job task logs. Keep it separate from a project cache so status/debug data is not mistaken for node output.

## Client/Job Model

The Python API uses `FarmLauncher(root=...)`, `LocalFarmClient(root)`, `Job(name)`, and `Task(name, command, metadata=None, env=None)`.

A job contains tasks and dependency edges. A task can spawn additional tasks during execution. The client can query job/task status and manage task/job lifecycle actions.

## Meshroom Integration

`LocalFarmSubmitter` converts graph nodes/chunks into ordered tasks. It can create placeholder, preprocess, expanding, chunk, and postprocess task types. When a node has not created chunks, a submitter may launch `meshroom_createChunks`; later tasks call `meshroom_compute` with the graph path and node/chunk selection.

The submitter can use Rez wrapping when configured. For a plain local farm, disable/avoid Rez assumptions and ensure the job environment contains Meshroom and plugin paths.

## Monitoring Checklist

- status file changes are visible to the submitting Meshroom process;
- task commands use the intended Python/Meshroom binaries;
- plugin config and `MESHROOM_*` paths are forwarded;
- `jobs/<jid>/tasks/<tid>.log` contains the command/error;
- a job with no active SUBMITTED/RUNNING tasks is terminal even if some tasks are `ERROR` or `STOPPED`.
