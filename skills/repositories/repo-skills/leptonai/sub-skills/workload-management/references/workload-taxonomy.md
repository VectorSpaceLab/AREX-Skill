# Workload Taxonomy

Lepton workloads consume remote DGX Cloud Lepton CPU/GPU capacity. Pick the workload type by lifetime, interaction pattern, replica model, and how much control the user needs over the runtime spec.

## Quick choice table

| Workload | Use when | Lifetime | Replica/capacity model | Main CLI |
| --- | --- | --- | --- | --- |
| Endpoint | The user needs a stable serving URL for inference or an HTTP container service. | Long-running; can scale to zero. | Autoscaled replicas or fixed replicas. | `lep endpoint ...` |
| Dev pod | The user needs an interactive machine for SSH, notebook, IDE, debugging, or exploration. | Long-running until stopped or removed. | Single pod; not a production traffic fanout. | `lep pod ...` |
| Batch job | The user needs a finite training, evaluation, processing, or sweep run. | Runs to completion or failure. | `parallelism`/`completions` workers; optional retries. | `lep job ...` |
| Ray cluster | The user needs a Ray head plus worker groups for distributed Python pipelines, actors, or Ray jobs. | Long-running but suspendable. | Head group plus one or more worker groups; optional autoscaler. | `lep raycluster ...` |
| Fine-tune job | The user wants guided model tuning using a trainer/template schema rather than a hand-authored job. | Runs to completion. | Job-like workers with trainer config. | `lep finetune ...` |
| Template | The user wants a predefined job/pod/endpoint spec rendered with parameters. | Not a workload itself. | Renders into endpoint, pod, or job spec. | `lep template ...` plus create `--template` |
| Node/resource shape | The user needs capacity, shape, node group, reservation, or storage visibility before scheduling. | Read-only capacity view. | Node groups, shapes, reservations, volumes. | `lep node ...` |
| Logs/events | The user is diagnosing a workload after it exists. | Read-only diagnostics. | Replica/time/query scoped. | `lep log get`, `lep endpoint events`, `lep job events` |

## Decision signals

### Endpoint

Choose endpoint for:

- "Deploy", "serve", "inference service", "chat endpoint", "embedding service", "HTTP route", "stable URL".
- A container that listens on a service port.
- Replica scaling, QPM scaling, GPU utilization scaling, scale-to-zero, rolling restart, header-based replica routing, load balancing, public/token/IP access, or endpoint visibility.

Default read-only plan:

```bash
lep endpoint list
lep endpoint status -n NAME
lep endpoint get -n NAME
lep endpoint events -n NAME
```

Mutation examples to plan, not run without confirmation:

```bash
lep endpoint create -n NAME --container-image IMAGE --container-command "COMMAND" --container-port 8080:tcp --resource-shape SHAPE
lep endpoint update -n NAME --container-image IMAGE
lep endpoint stop -n NAME
lep endpoint restart -n NAME
lep endpoint remove -n NAME
```

### Dev pod

Choose pod for:

- "SSH", "Jupyter", "interactive", "debug shell", "notebook", "remote VM-like environment", "IDE".
- A single long-lived workspace where the user controls the container command and ports.

Default read-only plan:

```bash
lep pod list --detail
lep pod get -n NAME
```

Mutation examples to plan, not run without confirmation:

```bash
lep pod create -n NAME --resource-shape SHAPE --container-image IMAGE
lep pod ssh -n NAME
lep pod stop -n NAME
lep pod remove -n NAME
```

Caveat: `lep pod ssh` actually launches local SSH. If the user only asked for a plan or debug advice, use `lep pod list --detail` and `lep pod get -n NAME` first.

### Batch job

Choose job for:

- "Run once", "training", "evaluation", "batch", "data processing", "sweep", "workers", "retries", "schedule", "TTL".
- Any task with a defined terminal state rather than serving traffic.

Default read-only plan:

```bash
lep job list
lep job get --id JOB_ID
lep job replicas --id JOB_ID
lep job nodes --id JOB_ID
lep job events --id JOB_ID
```

Mutation examples to plan, not run without confirmation:

```bash
lep job create -n NAME --container-image IMAGE --resource-shape SHAPE --command "COMMAND"
lep job stop --id JOB_ID
lep job start --id JOB_ID
lep job remove --id JOB_ID
```

### Ray cluster

Choose Ray cluster for:

- "Ray", "actor", "head", "worker group", "Ray job", "runtime_env", "autoscaling Ray", "distributed Python pipeline".
- Multi-stage Python workloads where users submit jobs after the cluster exists.

Default read-only plan:

```bash
lep raycluster list
lep raycluster get -n NAME
lep raycluster list-jobs -n NAME
```

Mutation examples to plan, not run without confirmation:

```bash
lep raycluster create -n NAME --head-resource-shape SHAPE --head-node-group NODE_GROUP -wg --group-name workers --resource-shape SHAPE --node-group NODE_GROUP --min-replicas 1
lep raycluster submit-job -n NAME -- python script.py
lep raycluster stop-job -n NAME --job-id RAY_JOB_ID
lep raycluster stop -n NAME
lep raycluster start -n NAME
lep raycluster remove -n NAME
```

### Fine-tune job

Choose fine-tune for:

- "Fine-tune", "trainer", "base model", "dataset URI", "LoRA/SFT recipe", "HF token secret", "W&B API key secret".
- Guided model training where the trainer schema should produce the relevant flags.

Default read-only plan:

```bash
lep finetune list
lep finetune get -i JOB_ID
lep finetune list-trainers
```

Mutation example to plan, not run without confirmation:

```bash
lep finetune create -n NAME --resource-shape SHAPE [trainer flags from template]
```

In `--file` mode, fine-tune create preserves trainer settings from the spec file and ignores trainer CLI flags.

## Capacity and shape selection

Before create/update commands, inspect shapes and node groups:

```bash
lep node resource-shape --purpose deployment
lep node resource-shape --purpose pod
lep node resource-shape --purpose job
lep node list
lep node list-nodes NODE_GROUP
lep node list-reservations NODE_GROUP
lep node storage --node-group NODE_GROUP
```

Use `--node-group`, `--node-id`, `--with-reservation`, queue priority, and preemption flags only when the user knows the capacity target. Node storage output is a capacity/mount-discovery aid; data transfer and secret setup belongs to the storage/secrets route.

## Template selection

Templates can render endpoint, pod, or job specs. Use them when the user refers to a named workflow template or asks for a reusable spec:

```bash
lep template list
lep endpoint create -n NAME --template TEMPLATE_ID --run "COMMAND"
lep pod create -n NAME --template TEMPLATE_ID --run "COMMAND"
lep job create -n NAME --template TEMPLATE_ID --run "COMMAND"
```

`lep template get` exists as a hidden command for retrieving template JSON, but normal users usually start with `lep template list` and a workload create command.
