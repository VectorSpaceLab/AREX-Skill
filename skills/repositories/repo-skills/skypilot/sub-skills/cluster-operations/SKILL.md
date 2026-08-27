---
name: cluster-operations
description: "Operate SkyPilot interactive clusters safely with CLI launch,
  exec, status, logs, queues, lifecycle cleanup, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cluster Operations

Use this sub-skill when the user wants to operate interactive SkyPilot clusters or cluster-local jobs through the CLI: launch, reuse, execute commands, inspect status, tail logs, view queues, cancel cluster jobs, configure autostop, stop/start, down, dry-run, or estimate cluster cost.

Do not use this sub-skill for deep task YAML schema design, managed jobs, SkyServe services, provider credential setup, Python SDK equivalents, or contributor test workflows. Route those to the sibling sub-skills instead.

## Read First

- For command sequences and safe defaults, read [references/cli-workflows.md](references/cli-workflows.md).
- For failure triage, read [references/troubleshooting.md](references/troubleshooting.md).
- For safe command suggestions, use [scripts/cluster_command_builder.py](scripts/cluster_command_builder.py).
- For task YAML fields and validation, route to the `task-yaml` sub-skill.
- For cloud credentials, Kubernetes, Slurm, SSH, storage, and GPU catalog issues, route to the `infrastructure-storage` sub-skill.
- For managed jobs with controller recovery, route to the `managed-jobs` sub-skill.
- For SDK/API-server equivalents, route to the `sdk-api-server` sub-skill.

## Operating Principles

- Prefer resource requirements over manual infrastructure pins: specify `--gpus`, `--cpus`, `--memory`, `--disk-size`, `--ports`, and `--use-spot` when relevant, then let SkyPilot choose cloud, region, zone, and instance type unless the user explicitly needs a provider or cluster backend.
- Use `sky launch --dryrun` before any new or expensive cluster launch; it exercises parsing and optimizer planning without launching cloud resources.
- Name reusable clusters with `sky launch -c <cluster> ...`; a matching cluster from `sky status` is reused instead of creating a new one.
- Use `sky exec <cluster> ...` for iterative run-command changes on an existing cluster. It syncs `workdir` when provided, but skips provisioning, setup commands, and file-mount syncing; rerun `sky launch -c <cluster> ...` when setup, resources, image, file mounts, or cluster shape changed.
- Use machine-readable output for automation: `sky status -o json`, `sky queue -o json`, and `sky cost-report -o json`. Use `sky logs --status` or bounded `--tail` for log checks rather than scraping tables.
- Always include a cleanup policy for interactive clusters: `--idle-minutes-to-autostop`, `sky autostop`, `sky stop`, or `sky down` depending on whether the cluster should be restartable.

## Command Router

- New interactive cluster: `sky launch --dryrun -c <cluster> <task.yaml>` first, then launch with autostop once the user approves cost and provider implications.
- Run more work on an existing cluster: `sky exec <cluster> <task.yaml>` or `sky exec <cluster> --workdir . <command>`.
- Inspect cluster health: `sky status --refresh -o json <cluster>` when cloud state may have changed, otherwise `sky status -o json <cluster>`.
- Inspect cluster jobs: `sky queue <cluster> -o json`, `sky logs <cluster> <job-id> --tail 200 --no-follow`, and `sky cancel <cluster> <job-id>` for cluster-local jobs.
- Preserve but stop billing for compute: `sky stop <cluster>`; restart later with `sky start <cluster>`.
- Delete cloud resources and attached disks: `sky down <cluster>` only after confirming the user no longer needs cluster disk state.

## Safety Checklist

Before suggesting commands that mutate cloud resources, confirm:

- The cluster name is correct and not a managed-jobs or SkyServe controller.
- The user understands whether `stop` is restartable and `down` is destructive.
- Expensive launches are dry-run first unless the user explicitly asks to launch.
- Manual `--infra`, region, zone, or `--instance-type` pins are intentional, not accidental optimizer bypasses.
- `--all`, `--all-users`, `--purge`, `--yes`, and autodown are justified and scoped.
- Secrets are passed with `--secret` or secret files, not embedded in public logs or command transcripts.

## Useful Helper

Use the bundled command builder for no-launch command planning:

```bash
python sub-skills/cluster-operations/scripts/cluster_command_builder.py debug-cycle \
  --cluster mycluster \
  --task-yaml task.yaml \
  --gpus A100:1 \
  --idle-minutes 30
```

The helper prints commands by default. It includes dry-run launch suggestions unless `--ready-to-launch` is provided, and it refuses to execute launch or destructive commands unless explicit execution and safety flags are set.
