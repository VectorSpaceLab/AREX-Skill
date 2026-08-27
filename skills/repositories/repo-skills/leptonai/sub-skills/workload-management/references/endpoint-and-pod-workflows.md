# Endpoint and Dev Pod Workflows

Use this reference for long-running serving endpoints and interactive dev pods. Both are workload resources, but they have different lifecycle semantics and diagnostics.

## Endpoint command surface

Prefer the visible endpoint group:

```bash
lep endpoint create -n NAME --container-image IMAGE [options]
lep endpoint list [--name PATTERN]
lep endpoint get -n NAME [--path OUTPUT_PATH]
lep endpoint status -n NAME [--detail] [--show-tokens]
lep endpoint update -n NAME [update options]
lep endpoint stop -n NAME
lep endpoint restart -n NAME
lep endpoint remove -n NAME
lep endpoint log -n NAME [--replica REPLICA_ID]
lep endpoint events -n NAME
```

A hidden legacy `lep deployment ...` group is kept for compatibility and exposes the same commands. Use `lep endpoint ...` in new instructions unless the user is debugging an older script that already uses `deployment`.

### Endpoint create plan

Minimum container-style endpoint:

```bash
lep endpoint create \
  -n NAME \
  --container-image IMAGE \
  --container-command "COMMAND_THAT_LISTENS_ON_PORT" \
  --container-port 8080:tcp \
  --resource-shape SHAPE
```

Important flags:

- `--file SPEC_JSON` loads an endpoint spec, then CLI overrides are applied.
- `--container-image IMAGE` is required when setting a container command. If no spec supplies a container and no image is provided, create fails.
- `--container-port PORT` accepts `8080` or `8080:tcp`; allowed protocol values are normalized by the model. Empty segments, non-integer ports, or extra colon segments fail locally.
- `--resource-shape SHAPE` chooses the resource. If omitted, endpoint creation falls back to the package default shape.
- `--replicas-static N`, `--autoscale-down N,SECONDS`, `--autoscale-gpu-util MIN,MAX,THRESHOLD`, and `--autoscale-qpm MIN,MAX,QPM` are mutually exclusive new autoscale modes.
- Deprecated autoscale options (`--min-replicas`, `--max-replicas`, `--no-traffic-timeout`, `--target-gpu-utilization`) cannot be mixed with the new autoscale modes.
- `--public` clears IP restrictions; `--ip-whitelist` restricts by IP/CIDR; `--tokens` is independent of both. Route access-control design to `storage-secrets-ingress` when the task is about ingress/IP/token policy rather than endpoint runtime.
- `--load-balance least-request|sticky-routing` selects load balancing. Update sends explicit nulls for the deselected policy so merge-patch does not preserve stale policy.
- `--header-based-routing [true|false]` enables/disables targeting a replica using `X-Lepton-Replica-Target`. Bare flag means true; typos such as `ture` fail at parse time.
- `--log-collection true|false` controls workload log collection when the workspace default is not desired.
- `--node-group`, `--node-id`, `--queue-priority`, `--can-be-preempted`, `--can-preempt`, `--with-reservation`, `--allow-burst-to-other-reservation`, `--replica-spread`, and `--shared-memory-size` control scheduling and capacity placement.

### Duplicate endpoints and rerun

Without `--rerun`, create checks for an existing endpoint name and exits before creating workspace token secrets, prompting, validating, deleting, or creating. Plan `lep endpoint update` for production changes.

With `--rerun`, create validates the fully assembled replacement spec before deleting the existing workload. Rerun deletes the old workload and creates a replacement, so it can cause downtime; do not suggest it for production unless the user explicitly accepts that behavior.

### Endpoint status and readiness

Use:

```bash
lep endpoint status -n NAME
lep endpoint status -n NAME --detail
lep endpoint get -n NAME
lep endpoint events -n NAME
```

Status prints created time, image, state, replica range, autoscaler details, public/token status, and replica readiness. In new endpoint API mode, standalone readiness and termination routes do not exist; status degrades to a note and per-replica state instead of treating the missing legacy routes as fatal.

Only use `--show-tokens` if the user explicitly asks to inspect endpoint tokens. Server responses may redact literal token values; do not treat redacted output as a usable access value.

### Endpoint update plan

Examples:

```bash
lep endpoint update -n NAME --container-image IMAGE
lep endpoint update -n NAME --replicas-static 2
lep endpoint update -n NAME --autoscale-down 1,3600s
lep endpoint update -n NAME --autoscale-qpm 1,3,2.5
lep endpoint update -n NAME --load-balance sticky-routing
lep endpoint update -n NAME --header-based-routing false
lep endpoint update -n NAME --public
lep endpoint update -n NAME --ip-whitelist 203.0.113.0/24
```

Update options are replacements, not incremental merges, for the fields they target. Example: supplying `--tokens` replaces the token list. For load balancing, a change to sticky routing must clear least-request and vice versa. If the backend reports `no valid field to update`, the CLI prints a clear `No changes applied` message and exits zero; treat that as a no-op, not a failure.

### Endpoint stop/restart/remove/log/events

```bash
lep endpoint stop -n NAME       # scales/stops; exits no-op if already stopped/stopping/deleting
lep endpoint restart -n NAME    # triggers restart
lep endpoint remove -n NAME     # deletes endpoint
lep endpoint log -n NAME        # selects first replica if not specified
lep endpoint log -n NAME --replica REPLICA_ID
lep endpoint events -n NAME
```

`lep endpoint log` is a live stream for one replica. If a user wants historical scoped logs, use `lep log get --endpoint NAME --start ... --end ...` from [logs-events-nodes.md](logs-events-nodes.md).

## Dev pod command surface

```bash
lep pod create -n NAME --resource-shape SHAPE [options]
lep pod list [--pattern REGEX] [--detail]
lep pod get -n NAME [--path OUTPUT_PATH]
lep pod ssh -n NAME
lep pod stop -n NAME
lep pod remove -n NAME
```

Dev pods are interactive, single-replica workspaces. They are not endpoint-style services for production traffic, and pod update is intentionally unsupported because changing pod resources can lose local state.

### Pod create plan

Minimum pod:

```bash
lep pod create \
  -n NAME \
  --resource-shape SHAPE \
  --container-image IMAGE
```

Useful options:

- `--template TEMPLATE_ID --run "COMMAND"` renders a pod spec from a template. `--run` requires `--template`, and `--template` cannot be combined with `--file`.
- `--file SPEC_JSON` loads a pod spec, then CLI overrides are applied.
- `--container-command "COMMAND"` is preserved by pod sanity checks.
- `--container-port PORT:PROTOCOL:STRATEGY[:STRATEGY]` exposes ports. Strategies include `proxy` and `hostmap`; only one proxy port takes effect. Port exposure can create security risk, so make auth/security explicit.
- `--resource-shape` is required unless the loaded spec already supplies one.
- `--mount`, `--env`, `--secret`, `--image-pull-secrets`, `--log-collection`, `--privileged`, node group, node ID, queue, preemption, reservation, and burst flags mirror endpoint/job scheduling concepts. Route detailed storage/secret syntax validation to `storage-secrets-ingress`.

Pod specs preserve user-provided container command and ports. The sanity check only warns and clears fields that do not take effect for pods, such as autoscaler or endpoint API tokens.

### Pod list/get/status workflow

There is no separate `lep pod status` command. Use:

```bash
lep pod list
lep pod list --detail
lep pod get -n NAME
```

`lep pod list --detail` prints SSH command, TCP port mapping, JupyterLab mapping, created time, state, owner, shape, and a resource utilization summary. If requested host ports have not been allocated yet, the table shows `Not Available` instead of rendering `ssh -p None`.

### Pod SSH workflow

Use `lep pod ssh -n NAME` only when the user actually wants to open SSH. The command checks that the pod is Running/Ready, finds a public IP, then searches for an allocated SSH host port. Failure modes:

- No public IP: use the web terminal link printed by the CLI when available.
- SSH port missing or host port not allocated: do not retry raw SSH. Re-run `lep pod list --detail`, `lep pod get -n NAME`, and wait for port allocation or recreate with the correct port exposure.
- SSH subprocess exits with an error: inspect stderr, status, and pod connectivity; the CLI notes that pod output may only work for default image/default command.

### Pod stop/remove

```bash
lep pod stop -n NAME
lep pod remove -n NAME
```

Stop uses the pod stopped flag and exits as a no-op if the pod is already stopped, stopping, deleting, or legacy NotReady-without-phase. Remove deletes the pod; confirm local-state and remote-resource implications before running it.

## Endpoint and pod SDK hints

From Python, after workspace context is configured:

```python
from leptonai.api.v2.client import APIClient
client = APIClient()

endpoints = client.deployment.list_all()
endpoint = client.deployment.get("endpoint-name")
pods = client.pod.list_all()
pod = client.pod.get("pod-name")
```

`client.deployment` and `client.pod` dispatch to legacy or new endpoint/devpod implementations based on the workspace feature flag. New endpoint/devpod modes intentionally report unsupported readiness, termination, events, or live DevPod log operations when the server surface lacks equivalent routes.
