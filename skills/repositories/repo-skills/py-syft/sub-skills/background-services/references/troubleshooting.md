# Background service troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `setup-status` reports missing credentials | Credentials/tokens/config not present or wrong scope. | Re-run `init`, create Drive and Gmail tokens with proper DO scopes. |
| Service appears stopped | Not started, crashed, or systemd user service absent. | Use `status`, `logs`, then `run-foreground` for visible errors. |
| Notifications not sent | Gmail token missing, bad scope, or interval not elapsed. | Verify Gmail token and config; run foreground notify service. |
| Auto-approval not triggered | Hash mismatch, file not in policy, peer mismatch. | Recompute hashes with bundled helper and inspect policy. |
| `logs` command argument mismatch | CLI/API changed or command expects a service name. | Use `syft-bg status`, `syft-bg run-foreground <service>`, or direct configured log paths. |
