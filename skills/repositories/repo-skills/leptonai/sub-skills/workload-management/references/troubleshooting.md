# Workload Troubleshooting

Use this file when a Lepton workload command is rejected, exits as a no-op, lacks logs, or cannot expose expected status/SSH details. Start with read-only list/get/status/log/event commands before proposing mutations.

## Duplicate workload and rerun behavior

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Endpoint NAME already exists. Use lep endpoint update ... or add --rerun ...` | Endpoint create found an existing endpoint and `--rerun` was not supplied. | Prefer `lep endpoint update -n NAME ...` for production changes. Use `--rerun` only after the user accepts delete-and-recreate downtime. |
| Rerun deletes but create temporarily conflicts with a still-deleting resource. | Backend deletion is asynchronous; create may see a 409 still-deleting response. | The CLI retries the create after a short wait in supported new endpoint/devpod paths. If still failing, inspect list/status and wait rather than repeatedly deleting. |
| Rerun with a spec file fails before any delete. | The CLI validates the fully assembled replacement spec before deleting. | Fix local spec/flag errors first. This is protective; do not bypass by manually deleting unless explicitly requested. |
| Job name matches multiple old jobs. | Jobs can share names; IDs are unique. | Use `lep job list --name-or-id NAME` then act on the exact `JOB_ID`. `lep job remove --name NAME` removes only the newest exact-name match; use `remove-all` only with exact filters and confirmation count. |

## New endpoint/devpod API readiness gaps

| Symptom | Meaning | Recovery |
| --- | --- | --- |
| Endpoint status prints a note that per-deployment readiness is unavailable. | In new endpoint API mode, standalone readiness/termination legacy routes do not exist; readiness is folded into per-replica status. | Use the per-replica status shown by `lep endpoint status -n NAME --detail`, plus `lep endpoint events -n NAME` and replica-scoped logs. |
| DevPod events or live DevPod log streaming are reported unsupported. | New DevPod API has no events route and no legacy live-text stream route with a discoverable replica ID. | Use `lep pod list --detail`, `lep pod get -n NAME`, web terminal hints, and historical/platform logs if available. Do not promise `lep pod log`; it is not a command in this CLI. |
| Pod update is unsupported. | Updating a pod can lose pod resources/local state. | Create a new pod or stop/remove/recreate only after the user accepts state loss. |

## Invalid container port options

Endpoint `--container-port` accepts:

```text
PORT
PORT:PROTOCOL
```

Examples:

```bash
lep endpoint create -n ep --container-image nginx:latest --container-port 8080:tcp --resource-shape SHAPE
lep endpoint create -n ep --container-image nginx:latest --container-port 8080 --resource-shape SHAPE
```

Failures and fixes:

- Empty segments such as `8080:` or `:tcp` are invalid. Use `8080:tcp`.
- More than one colon is invalid for endpoint ports. Use pod/job syntax only with the relevant command.
- Non-integer port names are invalid. Use a numeric port.
- If `--container-port` is set without a container-based endpoint, create fails. Supply a container image/spec.

Pod `--container-port` has a different syntax:

```text
PORT:PROTOCOL:STRATEGY[:STRATEGY]
```

Strategies include `proxy` and `hostmap`; only one proxy port takes effect. Job `--container-port` accepts repeated port/protocol values without pod expose strategies.

## Header-based routing booleans

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `is not a valid boolean` for `--header-based-routing` | Value typo such as `ture`, `yesplease`, or unsupported spelling. | Use a bare `--header-based-routing` to enable, or pass `true`/`false` explicitly. Values are case-insensitive. |
| Header routing appears enabled but requests do not target a replica. | Caller did not send the target header, or service did not return/persist replica ID. | Use `X-Lepton-Replica-Target: REPLICA_ID` and have the endpoint return `LEPTON_REPLICA_ID` if the client needs sticky follow-up calls. |

## Autoscale and replica option conflicts

New autoscale modes are mutually exclusive:

- `--replicas-static N`
- `--autoscale-down N,SECONDS`
- `--autoscale-gpu-util MIN,MAX,THRESHOLD`
- `--autoscale-qpm MIN,MAX,QPM`

Common failures:

| Symptom | Cause | Fix |
| --- | --- | --- |
| CLI says new autoscale options cannot be used together. | More than one new autoscale mode was supplied. | Pick one mode. Static replicas disable autoscaling; QPM/GPU modes scale within min/max; autoscale-down keeps fixed replicas and scales to zero after timeout. |
| CLI says deprecated and new autoscale options cannot be mixed. | Old flags like `--max-replicas`, `--no-traffic-timeout`, or `--target-gpu-utilization` were combined with a new mode. | Use only the new mode or only the old flags in one command. Prefer new modes for new plans. |
| `--autoscale-down` rejected. | Format is not `replicas,timeout` or timeout is under 60 seconds. | Use `--autoscale-down 1,3600s` or `--autoscale-down 1,3600`. |
| `--autoscale-gpu-util` rejected. | Format is wrong or threshold is outside 1-99. | Use `--autoscale-gpu-util 1,3,50%` or `1,3,50`. |
| `--autoscale-qpm` rejected. | Format is wrong or QPM threshold is not positive. | Use `--autoscale-qpm 1,3,2.5`. |

## No-op endpoint update

| Symptom | Meaning | Recovery |
| --- | --- | --- |
| `No changes applied` and exit code zero. | Backend reported no valid field to update, often because the requested value already matches current state. | Treat as success/no-op. If the user expected a change, inspect `lep endpoint get -n NAME` and ensure the intended field is represented by a supported update flag. |
| Other update error bubbles up. | The error is not a benign no-op. | Preserve the message, inspect current endpoint spec, and adjust flags. Do not classify arbitrary 400s as no-op. |

## Load balance update surprises

Switching load balancer policy requires clearing the deselected policy under JSON merge patch. The CLI intentionally sends an explicit `null` for the old policy when switching between `least-request` and `sticky-routing`. If a custom SDK script cannot switch policies, inspect the serialized payload and ensure the deselected policy is explicitly cleared while the selected policy is present.

## Pod SSH port missing

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `SSH port not found` | Pod is running/ready but the SSH container port is not exposed or host port is not allocated. | Run `lep pod list --detail` and `lep pod get -n NAME`. Wait for allocation, recreate with appropriate `--container-port`, or use web terminal. |
| `No public IP is found` | Pod has no reachable public IP. | Use the web terminal URL printed by the CLI when available or check workspace/network settings. |
| `lep pod list --detail` shows `Not Available` | Requested port exists but host port is still pending or absent. | Do not construct raw SSH manually. Wait, inspect pod get output, or recreate with correct port exposure. |
| SSH subprocess fails | Network/auth/image/command issue after the CLI attempted SSH. | Inspect stderr, pod status, public IP, host port, and whether the image/command supports SSH. |

## Job filter and state issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| State filter warns that no known states contain the pattern. | Typo or unsupported state prefix. | Use states/prefixes like `run`, `fail`, `complete`, `queue`, `await`, `pending`. |
| `--include-archived` cannot be used with `--state`. | The list command disallows combining archive mode and state filters. | Run one archive query without state, then narrow by name/user, or omit archive mode. |
| Archived list returns no results despite expected jobs. | Archive filtering often requires full user ID. | Use exact/full user ID from `lep job list` output. |
| `stop-all`/`remove-all` matches nothing. | These commands require exact user ID and exact name matching for safety. | Re-run `lep job list` to copy exact owner/name, then retry the filtered plan. |
| Start/stop no-op. | The job is already in a terminal or incompatible state. | Use `lep job get --id JOB_ID` and inspect state before retrying. |

## Ray cluster create/update errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| At least one worker group is required. | CLI create had no `-wg` blocks and no worker groups in the spec file. | Add `-wg --resource-shape SHAPE --node-group NODE_GROUP --min-replicas 1`. |
| Worker group flag must follow `-wg`. | A per-group flag appeared before a worker-group marker. | Put `-wg` before `--group-name`, `--resource-shape`, `--node-group`, etc. |
| Duplicate worker group name. | Same group name used more than once. | Give unique group names or target one existing group by name/index. |
| `--max-replicas` rejected on update. | Autoscaler is not enabled. | Enable autoscaler at create time or update only min replicas/segment count. |
| `--segment-count` rejected. | Autoscaler is enabled, count is non-positive, or it does not divide min replicas. | Disable autoscaler for segment-count workflows and choose a divisor of min replicas. |
| Ray submit-job says entrypoint required. | Missing `-- ENTRYPOINT...` after submit-job flags. | Add `-- python script.py ...`; everything after `--` becomes the Ray entrypoint. |
| Runtime env parse failure. | `--runtime-env` file is not YAML mapping, `--runtime-env-json` is not a JSON object, or both were specified. | Supply exactly one runtime-env source and validate it as a mapping. |

## Fine-tune creation surprises

| Symptom | Cause | Fix |
| --- | --- | --- |
| Trainer flags unavailable in `--file` mode. | Fine-tune create disables dynamic trainer option injection when loading a spec file. | Edit the spec file or omit `--file` and pass trainer flags generated from the template schema. |
| `--hf-token` or `--wandb-api-key` behaves unexpectedly. | The flag expects the **secret name**, not the raw token/key. | Create/manage the secret through the storage/secrets route, then pass the secret name. |
| Archived fine-tune delete rejected. | Archived fine-tune jobs cannot be deleted. | Treat them as historical records; delete only alive jobs by ID. |

## Logs need replica/time/tail scope

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No deployment name, job id, job name or replica id provided` | `lep log get` lacked a workload selector. | Add exactly one of `--endpoint`, `--job`, or `--job-name`. |
| Error says only one workload selector can be specified. | Multiple selectors were combined. | Choose one workload, then optionally add `--replica`. |
| No logs found. | Time range, query, job archive scope, or replica is too narrow/wrong. | Broaden `--start/--end`, remove `--query`, verify replica ID, and inspect events/status. |
| End time must be greater than start time. | Parsed timestamps are reversed. | Use UTC-aware ranges like `--start today --end now`. |
| Large log command is slow. | Historical log fetch is split into time windows; workers apply only without deprecated `--limit`. | Keep time range narrow, add `--query`, use `--workers`, and avoid `--limit`. |
| Need bulk logs. | `lep log get` is intended for quick scoped viewing, not archive download. | Use workspace log export instead of trying to fetch huge ranges through the CLI. |

## Validation sequence before risky recovery

When a user asks to "fix" a failed workload, collect:

1. Workload type and unique name/ID.
2. `list`/`get`/`status` output.
3. Shape/node group context if scheduling is involved.
4. Events.
5. Replica/node IDs.
6. Narrow logs with explicit time/query/replica.
7. Proposed mutation command with expected side effects and confirmation.
