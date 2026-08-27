# Logs, Events, Nodes, Shapes, and Capacity

Use this reference for diagnostics and capacity discovery around workloads. Prefer scoped, read-only diagnostics before planning any restart, stop, delete, or rerun.

## Log command families

Lepton has two log styles:

1. **Direct live stream for one replica** through the workload command family:

   ```bash
   lep endpoint log -n ENDPOINT_NAME [--replica REPLICA_ID]
   lep job log --id JOB_ID [--replica REPLICA_ID]
   ```

   If no replica is supplied, the CLI selects the first replica after listing replicas. Use this for quick live tailing. It can stream until interrupted and may end if the workload has not started or has already finished.

2. **Historical, time-scoped logs** through `lep log get`:

   ```bash
   lep log get --endpoint ENDPOINT_NAME --start today --end now
   lep log get --endpoint ENDPOINT_NAME --replica REPLICA_ID --start "today 13:00" --end now --query error
   lep log get --job JOB_ID
   lep log get --job-name JOB_NAME --start yesterday --end today
   lep log get --job JOB_ID --path ./logs --workers 32
   ```

   `lep log get` is intended for quick, scoped viewing. It is not recommended for downloading large-volume logs; use workspace log export outside this skill for bulk exports.

## Historical log scoping rules

- Specify exactly one workload selector among endpoint, job ID, job name, or hidden job-history selector. A replica may be added to endpoint/job scope.
- For jobs, `--start` and `--end` can be omitted. The CLI uses job creation time and completion time when available; if the job has not completed, end defaults to `now`.
- For endpoints and replicas, provide explicit `--start` and `--end` or accept defaults carefully: missing end becomes `now`, missing start becomes `today`.
- Time inputs are interpreted as UTC for `lep log get`; supported keywords include `now`, `today`/`td`, and `yesterday`/`yd`, with optional time-of-day suffixes.
- Date-time inputs accept forms like `2024-12-25 13:10:01.123456` or `2024/12/25 13:10:01.123456`.
- `--query` filters log content server-side.
- `--without-timestamp` suppresses timestamps in output.
- `--workers` controls concurrent fetch workers when `--limit` is not used; default behavior caps at 32 workers.
- `--limit` and the interactive next/last/time+/time- workflow are deprecated. Avoid building new plans around them.
- When saving logs with `--path`, the CLI writes a text file and prints a time range and line count summary.

Validation checks before log fetch:

```bash
lep endpoint status -n ENDPOINT_NAME
lep job get --id JOB_ID
lep job replicas --id JOB_ID
lep endpoint status -n ENDPOINT_NAME --detail
```

If a replica is supplied, confirm it appears in the workload's replica list/status. If no logs are found, adjust time range, query, and replica scope before assuming the workload produced no output.

## Events

Events are structured workload lifecycle messages and often explain scheduling, image pull, readiness, or termination issues better than logs alone.

Endpoint events:

```bash
lep endpoint events -n ENDPOINT_NAME
```

Job events:

```bash
lep job events --id JOB_ID
```

Both print event type, reason, regarding object, count, and last observed time. In new endpoint API mode, endpoint events are exposed, but new DevPod API events are not exposed; use pod status/list/get and platform terminal hints for dev pod diagnostics.

## Replicas and nodes for workload diagnosis

Endpoint:

```bash
lep endpoint status -n ENDPOINT_NAME
lep endpoint log -n ENDPOINT_NAME --replica REPLICA_ID
```

Job:

```bash
lep job replicas --id JOB_ID
lep job nodes --id JOB_ID
lep job log --id JOB_ID --replica REPLICA_ID
```

`lep job replicas` prints replica ID and node ID. `lep job nodes` prints the sorted node IDs for the job. Use these before asking for logs from a specific replica.

## Node group and shape discovery

Capacity discovery commands:

```bash
lep node list
lep node list --node-group PATTERN
lep node list-nodes NODE_GROUP
lep node list-reservations NODE_GROUP
lep node resource-shape
lep node resource-shape --purpose deployment
lep node resource-shape --purpose pod
lep node resource-shape --purpose job
lep node resource-shape --node-group NODE_GROUP --purpose job
lep node storage --node-group NODE_GROUP
```

Interpretation:

- `lep node list` shows node groups with healthy/error/total nodes, Lepton-managed vs BYOC type, and aggregate GPU/CPU/memory/disk usage.
- GPU `avail` only counts idle GPUs on nodes that are ready, healthy, and schedulable; unavailable nodes do not contribute available GPUs even if they report idle hardware.
- `lep node list-nodes NODE_GROUP` expands to per-node provider/region/status and resource usage.
- `lep node list-reservations NODE_GROUP` shows desired/approved/reserved node counts, reserved node IDs, GPU usage, users, and creator/time. Reservation status values include `Reserved`, `Reserving`, `WaitingEffective`, `PendingApproval`, `Rejected`, and `Expired`.
- `lep node resource-shape` lists shapes per node group and tags whether each shape is usable for pod, endpoint/deployment, or job purposes.
- `lep node storage` lists node-group volumes and their storage type. It is a discovery command only; file transfer, volume lifecycle, and secrets belong to `storage-secrets-ingress`.

Use shape names exactly as returned by `lep node resource-shape` when constructing create/update commands.

## Template and shape interaction

Templates may already specify a resource shape. When a create command also supplies a resource-shape flag, the CLI applies the explicit flag as an override. If neither template/spec nor CLI supplies a required shape for pods/jobs/fine-tune jobs, create fails and prints the available shape list.

## SDK log and capacity surfaces

Read-only SDK examples after workspace context is configured:

```python
from leptonai.api.v2.client import APIClient
client = APIClient()

# Historical logs. start/end are nanosecond epoch values at the API layer.
logs = client.log.get_log(name_or_job="job-id", start=START_NS, end=END_NS, q="error")

# Time-series logs.
series = client.log.get_log_time_series(name_or_deployment="endpoint-name", start=START_NS, end=END_NS, interval_ms=60000)

# Shapes and node groups.
shapes = client.shapes.list_shapes(purpose="job")
node_groups = client.nodegroup.list_all()
```

The SDK log resource chooses the correct endpoint/deployment query parameter depending on whether the workspace is using the new endpoint API. Do not hard-code legacy deployment log query keys in custom scripts.

## Diagnostic playbooks

### Endpoint not ready

1. `lep endpoint status -n NAME --detail`.
2. If status says standalone readiness is unavailable, inspect per-replica status in the same output and use events.
3. `lep endpoint events -n NAME`.
4. `lep endpoint log -n NAME --replica REPLICA_ID` or `lep log get --endpoint NAME --replica REPLICA_ID --start ... --end ...`.
5. Check port, command, resource shape, image pull secrets, and autoscale settings before proposing update/restart.

### Job failed or stuck

1. `lep job get --id JOB_ID`.
2. `lep job events --id JOB_ID`.
3. `lep job replicas --id JOB_ID` and `lep job nodes --id JOB_ID`.
4. `lep log get --job JOB_ID --query error` or replica-scoped `lep job log --id JOB_ID --replica REPLICA_ID`.
5. Check state filters, archived mode, retry counts, node group availability, and start schedule.

### Pod cannot be reached over SSH

1. `lep pod list --detail`.
2. Confirm SSH command is present and does not show `Not Available`.
3. `lep pod get -n NAME` to inspect state and port status.
4. If public IP or host port is missing, wait for allocation or use the web terminal hint. Do not construct `ssh -p None`.
