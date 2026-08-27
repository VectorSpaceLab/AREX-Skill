# CLI Operations Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| CLI says to run `rllm setup` | Deprecated alias wording | Run `rllm model setup` instead. |
| Configured provider works in one shell but not another | Different Python/env or `RLLM_HOME` | Inspect `RLLM_HOME` and run `rllm model show` in the active environment. |
| `rllm login` succeeds but eval has no live UI | UI disabled or no saved token in active state | Use `--ui`, confirm login in same `RLLM_HOME`, or run with `--no-ui` and local saved episodes. |
| `rllm init` would overwrite files | Existing project directory | Choose a new output directory or get explicit overwrite/cleanup approval. |
| `rllm agent` cannot find custom agent | Registry name/import path mismatch or package not installed | Prefer `module:object` for debugging; install the scaffold package editable; then register by stable name. |
| `rllm view` cannot load results | Path points at aggregate JSON vs episodes dir, or files were disabled | Re-run eval with `--save-episodes` and pass the correct output/episodes path. |
| Snapshot command fails on backend | Backend does not support snapshots or lacks credentials | Use `--no-snapshot` for execution, or choose a supported backend and configure credentials. |
