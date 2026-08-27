# Logging and Sidecars

## Logs CLI

Flow scripts expose a `logs` group:

```bash
python flow.py logs show FlowName/RunID/StepName/TaskID
python flow.py logs scrub FlowName/RunID/StepName/TaskID
```

Use `show` for stdout/stderr inspection and `scrub` only when intentionally removing stored logs.

## Sidecars

Metaflow sidecars support background services such as log saving, heartbeat, debug logging, and monitoring. Cards can also use subprocesses to render/refresh. When diagnosing card or log issues, distinguish:

- user step code failed,
- card render subprocess failed or timed out,
- sidecar failed to start or flush,
- datastore/metadata provider could not store or retrieve outputs.

For cloud-deployed tasks, logs may live in a remote datastore or provider-specific service. Verify the same profile/datastore used by the run.
