# Job troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Submitter/owner not recognized | Peer not approved or synced. | Route to auth/sync first. |
| Submission aborted | Pre-submit scan found risky code. | Review scan; use `force_submission` only with explicit acceptance. |
| Ambiguous folder entrypoint | No `main.py` and multiple root Python files. | Pass `entrypoint`. |
| Dependency install fails on DO | Missing package or bad version. | Add `dependencies`, align versions, inspect generated run command. |
| No outputs visible to DS | DO did not share outputs or job failed. | Use `share_outputs_with_submitter=True` and check owner-side job state. |
| Logs not visible | Logs are separately controlled. | Use `share_logs_with_submitter=True` only when appropriate. |
