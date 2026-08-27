# Job, Ray, Fine-Tune, and Template Workflows

Use this reference for finite workloads, distributed Ray workflows, guided fine-tuning, and reusable templates. Always inspect list/get state before planning mutations.

## Batch jobs

Batch jobs run to a terminal state and can use multiple workers. They are the default choice for training, evaluation, processing, sweeps, and scripted one-off tasks.

### Command surface

```bash
lep job create -n NAME --container-image IMAGE --resource-shape SHAPE --command "COMMAND"
lep job list [filters]
lep job get (--id JOB_ID | --name NAME) [--include-archived] [--path OUTPUT_PATH]
lep job replicas --id JOB_ID
lep job nodes --id JOB_ID
lep job log --id JOB_ID [--replica REPLICA_ID]
lep job events --id JOB_ID
lep job stop --id JOB_ID
lep job start --id JOB_ID
lep job remove (--id JOB_ID | --name NAME) [--include-archived]
lep job stop-all --user USER_ID [filters]
lep job remove-all --user USER_ID [filters]
lep job clone --id JOB_ID [--include-archived]
```

### Create plan

Common single-worker job:

```bash
lep job create \
  -n NAME \
  --container-image IMAGE \
  --resource-shape SHAPE \
  --command "python train.py"
```

Useful create flags:

- `--file SPEC_JSON` loads a job spec; `--template TEMPLATE_ID --run "COMMAND"` renders one from a template. `--run` requires `--template`, and `--template` cannot be combined with `--file`.
- `--container-image IMAGE` defaults to the package job base image only when no image is supplied by CLI or spec.
- `--command "..."` is wrapped as `/bin/bash -c ...`.
- `--container-port PORT[:PROTOCOL]` accepts repeated values for exposed job ports.
- `--resource-shape SHAPE` is required unless the spec already supplies one.
- `--num-workers N` sets both completions and parallelism and enables intra-job communication.
- `--segment-count N` is for GB200 node groups; it requires `--num-workers > 1`, must be in `[1, num_workers)`, and must divide `num_workers`.
- `--max-failure-retry` controls per-worker retries; `--max-job-failure-retry` controls whole-job retries.
- `--ttl-seconds-after-finished` defaults to 72 hours when not otherwise set.
- `--start-at` supports local-time strings by default and `UTC:` prefix for UTC scheduling.
- Node group, node ID, queue, preemption, reservation, burst, shared memory, log collection, visibility, privileged, env, secret, mount, and image-pull-secret flags mirror other workload families.

### Job listing and filters

`lep job list` supports server-side filters:

```bash
lep job list --state Running --user alice --name-or-id train --node-group h100
lep job list --include-archived --name-or-id train
```

Filter behavior:

- `--state` is case-insensitive prefix matching against states such as `Starting`, `Running`, `Failed`, `Completed`, `Stopped`, `Stopping`, `Deleting`, `Deleted`, `Restarting`, `Archived`, `Queueing`, `Awaiting`, and `PendingRetry`.
- Unknown state patterns warn but do not block parsing.
- `--user` is a case-insensitive prefix for list, but `stop-all` and `remove-all` require exact user IDs.
- `--name-or-id` is a case-insensitive substring for list.
- `--node-group` is a case-insensitive substring and resolves node groups before querying.
- `--include-archived` switches query mode to alive-and-archive and cannot be combined with `--state` in the list command. Archived job filtering works best with full user ID.

### Get, stop/start, and remove

`lep job get` requires exactly one of `--id` or `--name`; `--path` can save the spec only when exactly one job matches.

`lep job stop --id JOB_ID` sets `spec.stopped=true`. It is a no-op if the job is already stopped, stopping, failed, deleting, deleted, archived, or completed. `lep job start --id JOB_ID` sets `spec.stopped=false` only when the current job is stopped.

`lep job remove --name NAME` removes only the newest exact-name match. Use `remove-all` only with exact filters and a confirmation count. `stop-all` and `remove-all` print matched jobs and require the user to enter the number of jobs to affect.

### Job diagnostics

```bash
lep job replicas --id JOB_ID
lep job nodes --id JOB_ID
lep job log --id JOB_ID --replica REPLICA_ID
lep job events --id JOB_ID
lep log get --job JOB_ID
lep log get --job-name NAME --start today --end now
```

Direct `lep job log` streams one replica. Historical `lep log get` can infer the job time range from creation/completion when `--job` or `--job-name` is used and `--start`/`--end` are omitted.

## Ray clusters

Ray clusters provide a head node group and one or more worker groups, plus Ray job submission into the cluster.

### Command surface

```bash
lep raycluster create -n NAME [head flags] -wg [worker flags]
lep raycluster list [--name PATTERN]
lep raycluster get -n NAME [--detail] [--path OUTPUT_PATH]
lep raycluster update -n NAME -wg [worker update flags]
lep raycluster stop -n NAME
lep raycluster start -n NAME
lep raycluster remove -n NAME
lep raycluster submit-job -n NAME [Ray job flags] -- ENTRYPOINT...
lep raycluster list-jobs -n NAME
lep raycluster stop-job -n NAME --job-id RAY_JOB_ID
```

### Create plan

A CLI-only Ray cluster must include at least one worker group:

```bash
lep raycluster create \
  -n NAME \
  --head-resource-shape HEAD_SHAPE \
  --head-node-group HEAD_NODE_GROUP \
  --head-image IMAGE \
  --ray-version RAY_VERSION \
  -wg --group-name workers --resource-shape WORKER_SHAPE --node-group WORKER_NODE_GROUP --min-replicas 1
```

Important create details:

- `--file SPEC_JSON` loads a spec and allows CLI overrides.
- Default built-in Ray images determine the Ray version automatically; do not pass `--ray-version` for those default images. For custom images, provide or preserve `ray_version`.
- Head group flags use `--head-*`: resource shape, shared memory, mounts, env/secrets, node group, allowed nodes, reservation, image, command, burst, and privileged.
- Worker groups are introduced by `-wg` or `--worker-group`; flags following the marker belong to that group until the next marker.
- Worker group flags include `--index`, `--group-name`, `--image`, `--command`, `--resource-shape`, `--shared-memory-size`, `--min-replicas`, `--max-replicas`, `--segment-count`, `--node-group`, `--allowed-nodes`, `--reservation`, `--allow-burst`, `--privileged`, `--env`, `--secret`, and `--mount`.
- New worker groups require resource shape and exactly one node group. Duplicate worker group names are rejected.
- `--enable-autoscaler` requires `--autoscaler-worker-idle-timeout >= 60`; with autoscaler, worker `--max-replicas` must exceed min replicas.
- Without autoscaler, `--segment-count` can be used and must evenly divide min replicas.

### Updating Ray clusters

Ray update supports worker group replica/segment patches and suspend/start/stop behavior. CLI update examples:

```bash
lep raycluster update -n NAME -wg --group-name workers --min-replicas 2
lep raycluster update -n NAME -wg --group-name workers --min-replicas 2 --max-replicas 8
lep raycluster stop -n NAME
lep raycluster start -n NAME
```

If there is exactly one existing worker group and one update block, the group name can be inferred. Otherwise every update block needs `--group-name`. `--max-replicas` is only valid when autoscaler is enabled. `--segment-count` is only valid when autoscaler is disabled and must divide `--min-replicas`.

### Ray job submission

Submit Ray jobs after the cluster exists:

```bash
lep raycluster submit-job -n CLUSTER -- python script.py --arg value
lep raycluster submit-job -n CLUSTER --submission-id ID --runtime-env runtime.yaml -- python script.py
lep raycluster submit-job -n CLUSTER --runtime-env-json '{"pip": ["package"]}' --no-wait -- python script.py
lep raycluster list-jobs -n CLUSTER
lep raycluster stop-job -n CLUSTER --job-id RAY_JOB_ID
```

Rules:

- Everything after `--` is treated as the Ray job entrypoint.
- Specify only one of `--runtime-env` or `--runtime-env-json`.
- `--working-dir` overrides the runtime env working directory.
- `--metadata-json` and `--entrypoint-resources` must parse to JSON objects.
- Without `--no-wait`, the CLI streams Ray job logs and exits nonzero if the Ray job status is not succeeded.

## Fine-tune jobs

Fine-tune jobs are guided job-like runs with trainer configuration.

### Command surface

```bash
lep finetune list [filters]
lep finetune get -i JOB_ID [--include-archived] [--path OUTPUT_PATH]
lep finetune create -n NAME --resource-shape SHAPE [job flags] [trainer flags]
lep finetune delete -i JOB_ID
lep finetune list-trainers
```

`list-trainers` is hidden but supported and useful when the user needs to discover trainer IDs or the default trainer.

### Listing and getting fine-tune jobs

```bash
lep finetune list --q NAME_SUBSTRING --status Running --node-group h100 --created-by USER
lep finetune list --include-archived
lep finetune get -i JOB_ID --include-archived
```

Filters include substring query (`--q`), label selector (`--query`), repeated status, repeated node group, creator, page, page size, and include-archived query mode.

### Fine-tune create plan

Common shape:

```bash
lep finetune create \
  -n NAME \
  --resource-shape SHAPE \
  --num-workers 1 \
  [trainer flags injected from the selected trainer template]
```

Important create details:

- Without `--file`, trainer flags are generated dynamically from the trainer template JSON schema. The default trainer is discovered from the API when possible and otherwise falls back to a known default trainer ID.
- `--template` is hidden and selects the trainer template for dynamic flags.
- `--file SPEC_JSON` loads a fine-tune job spec and disables trainer-flag injection. If trainer CLI flags are also present, they are ignored with a warning.
- `--hf-token SECRET_NAME` injects an `HF_TOKEN` environment variable from a named secret. It expects a secret name, not a raw token value.
- `--wandb-api-key SECRET_NAME` injects `WANDB_API_KEY` from a named secret, not a raw key.
- Job scheduling flags mirror batch jobs: resource shape, workers, segment count, mount, shared memory, node group, node ID, queue, preemption, reservation, burst, and visibility.
- `--resource-shape` is required unless the loaded spec supplies one.

### Delete behavior

```bash
lep finetune delete -i JOB_ID
```

Archived fine-tune jobs cannot be deleted; `--include-archived` on delete is deprecated and errors. Treat archived fine-tune records as historical metadata rather than active resources.

## Templates

Templates are shared spec generators, not running workloads.

```bash
lep template list
lep template get -i TEMPLATE_ID --public --path template.json
lep template get -i TEMPLATE_ID --private
```

Template list shows public and private templates and the workload type (`endpoint`, `pod`, `job`, or other). `template get` is hidden and auto-detects public first when neither namespace is specified. Use template output to build create plans, but do not run a template-rendering create command until the user has confirmed the resulting workload and cost/side effects.

## SDK surfaces

Read-only examples after workspace context is configured:

```python
from leptonai.api.v2.client import APIClient
client = APIClient()

jobs = client.job.list_all(q="train")
job = client.job.get("job-id")
rayclusters = client.raycluster.list_all()
finetunes = client.finetune.list_all(q="experiment")
trainers = client.finetune.list_trainers(default_only=False)
templates = client.template.list_public() + client.template.list_private()
```

Mutation methods exist (`create`, `update`, `delete`, start/stop patches through CLI), but build and serialize payloads for review before using them in live workspace scripts.
