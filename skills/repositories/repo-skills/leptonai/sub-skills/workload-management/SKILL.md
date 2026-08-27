---
name: workload-management
description: "Operate Lepton endpoint, pod, job, Ray cluster, fine-tune,
  template, node, log, event, and workload status workflows from safe CLI and
  SDK plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Workload Management

Use this sub-skill when a task involves Lepton compute workloads: endpoint/deployment serving, dev pods, batch jobs, Ray clusters, fine-tuning jobs, templates, resource shapes, node capacity, workload logs, events, status checks, restarts, stops, starts, and removal plans.

Do **not** run live cloud mutations unless the user has explicitly asked for them and the root or `cli-operations` safety route has handled confirmation. This sub-skill supplies workload-specific commands and validation checks; generic workspace authentication belongs to `workspace-and-auth`, and generic command confirmation/output handling belongs to `cli-operations`.

## Choose the route

- Read [references/workload-taxonomy.md](references/workload-taxonomy.md) when the user is choosing between endpoint, dev pod, batch job, Ray cluster, and fine-tuning job.
- Read [references/endpoint-and-pod-workflows.md](references/endpoint-and-pod-workflows.md) for `lep endpoint`/legacy `lep deployment` and `lep pod` create/list/get/status/update/stop/restart/remove/log/SSH flows.
- Read [references/job-ray-finetune-workflows.md](references/job-ray-finetune-workflows.md) for batch job, Ray cluster, Ray job, fine-tune job, and template workflows.
- Read [references/logs-events-nodes.md](references/logs-events-nodes.md) for historical logs, streaming logs, events, replicas, nodes, node groups, resource shapes, and node-group storage visibility.
- Read [references/troubleshooting.md](references/troubleshooting.md) when create/update/list/log/SSH/status commands fail or produce surprising no-op behavior.
- Use [scripts/build_workload_command.py](scripts/build_workload_command.py) to produce dry-run command examples for endpoint, job, and pod basics without executing `lep`.

## Workload task mapping

| User intent | Best workload route | First read-only command |
| --- | --- | --- |
| Serve an HTTP model, embedding service, or custom container continuously | Endpoint | `lep endpoint list` then `lep endpoint status -n NAME` |
| Open a personal interactive machine, notebook, SSH shell, or IDE target | Dev pod | `lep pod list --detail` then `lep pod get -n NAME` |
| Run training, evaluation, processing, or sweeps to completion | Batch job | `lep job list` then `lep job get --id JOB_ID` |
| Run distributed Python/Ray pipelines with a head and worker groups | Ray cluster | `lep raycluster list` then `lep raycluster get -n NAME` |
| Launch guided model fine-tuning from a trainer/template schema | Fine-tune job | `lep finetune list` then `lep finetune get -i JOB_ID` |
| Find valid shapes/capacity before creating workloads | Nodes/shapes | `lep node resource-shape --purpose deployment|pod|job` |
| Diagnose workload output or failures | Logs/events | `lep log get ...`, `lep endpoint events -n NAME`, or `lep job events -i JOB_ID` |

## Safe workload workflow

1. **Identify the workload type.** If the user says "service", "API", "serve", "replicas", "QPM", or "scale to zero", prefer endpoint. If they say "SSH", "Jupyter", "debug machine", or "interactive", prefer pod. If they say "run once", "training job", "sweep", or "completion", prefer job. If they say "Ray actors", "Ray job", "head/worker", or "autoscaling Ray", prefer Ray cluster. If they say "fine-tune", "trainer", "base model", or "dataset recipe", prefer fine-tune.
2. **Gather read-only state first.** Use list/get/status commands and shape/node discovery before proposing create/update/stop/delete commands.
3. **Plan mutations as commands, not execution.** Show the exact `lep` command, expected side effects, required workspace context, and whether it may create cost, stop compute, delete resources, or replace fields.
4. **Validate workload-specific arguments.** Check create/update flags for container image/name, resource shape, port syntax, autoscale exclusivity, header-routing booleans, job filters, Ray worker group structure, and log time/replica scope.
5. **Use scoped diagnostics.** Prefer status/get, replicas/nodes, events, and time-scoped logs over broad log downloads or unscoped destructive operations.

## Core command families

- Endpoint/deployment: `lep endpoint create|list|get|status|update|stop|restart|remove|log|events`; the hidden legacy alias `lep deployment ...` maps to the same command family for compatibility, but prefer `lep endpoint` in new plans.
- Dev pod: `lep pod create|list|get|ssh|stop|remove`; use `lep pod list --detail` for SSH/TCP/JupyterLab columns and `lep pod get -n NAME` for JSON details.
- Batch job: `lep job create|list|get|stop|start|remove|remove-all|stop-all|clone|log|replicas|nodes|events`.
- Ray cluster: `lep raycluster create|list|get|update|start|stop|remove|submit-job|list-jobs|stop-job`.
- Fine-tune: `lep finetune list|get|create|delete|list-trainers`; create dynamically injects trainer flags from a trainer template unless `--file` mode is used.
- Templates and capacity: `lep template list`, hidden `lep template get`, `lep node list`, `lep node list-nodes`, `lep node list-reservations`, `lep node resource-shape`, `lep node storage`.
- Historical logs: `lep log get --endpoint NAME ...`, `lep log get --job JOB_ID ...`, or `lep log get --job-name NAME ...`; use direct `lep endpoint log` / `lep job log` for replica live-stream style commands.

## Python SDK surfaces

For scripts that need API objects instead of shell commands, use `APIClient()` after workspace context is configured by the auth route. The workload attributes are:

- `client.deployment`: endpoint/deployment API, dispatching to the new endpoint implementation when enabled.
- `client.pod`: dev pod API, dispatching to the new devpod implementation when enabled.
- `client.job`, `client.raycluster`, `client.finetune`, `client.template`, `client.shapes`, `client.nodegroup`, and `client.log` for the matching resource families.

Keep SDK examples read-only unless the user has explicitly requested a mutation. Use `.safe_json(...)` or model serialization for reviewable payloads before create/update/delete.

## Boundaries and cross-routes

- Storage/file transfer, secrets, ingress/canary routing, IP allowlist design, and storage mount validation are owned by `storage-secrets-ingress`; this sub-skill only notes workload flags that reference mounts, secrets, tokens, or IP allowlists.
- Authentication, workspace selection, environment variables, and token redaction are owned by `workspace-and-auth`.
- Generic confirmation rules, command tree discovery, output capture, and destructive-command confirmation are owned by root/`cli-operations`; apply them before running any create/update/stop/start/remove/delete command.
