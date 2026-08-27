# LocalFarm Troubleshooting

- **`status` cannot connect:** start the daemon with the same `--root`; inspect `farm.pid`, `backend.port`, and `backend.log`.
- **Windows launch fails:** the current backend uses Unix fork-style daemonization; use another submitter or run LocalFarm on Unix.
- **Job is submitted but no task runs:** inspect the job's task set and dependencies; check that the backend process is alive and that the command is not waiting on a missing dependency.
- **Chunk task creation fails:** verify the node created chunks, the submitter is registered, and `meshroom_createChunks`/`meshroom_compute` are resolvable in the job environment.
- **Task command cannot import plugin node:** forward `MESHROOM_PLUGINS_PATH`, `MESHROOM_NODES_PATH`, template paths, and any plugin config/process environment into the job.
- **Status does not update in the UI:** verify the UI and farm share the same cache/status filesystem; then use `meshroom_status` independently.
- **Job has errors:** inspect per-task logs before restarting. Use `restartErrorTasks()` for recoverable task failures; use `interruptJob()`/`restartJob()` when the job graph itself is invalid.
- **Rez wrapper changes behavior:** compare the wrapped command and current `REZ_*` environment. For a plain Python farm, disable Rez wrapping rather than adding arbitrary packages.
