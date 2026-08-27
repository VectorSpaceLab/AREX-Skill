---
name: infrastructure-storage
description: "Configure and troubleshoot SkyPilot clouds, Kubernetes, Slurm, SSH
  node pools, resources, GPUs, workspaces, storage, and volumes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Infrastructure And Storage

Use this sub-skill when the user needs to configure, select, or troubleshoot SkyPilot infrastructure and data surfaces: cloud credentials, Kubernetes contexts, Slurm clusters and partitions, SSH node pools, workspaces, GPU/resource availability, `sky check`, `sky gpus`, object-store storage, file mounts, and volumes.

## Start Here

1. Read [references/infrastructure-reference.md](references/infrastructure-reference.md) for supported infrastructure forms, resource-selection rules, GPU/catalog commands, workspace behavior, object-store storage, and volumes.
2. Use [scripts/resource_checklist.py](scripts/resource_checklist.py) to print a no-credential preflight checklist for a provider, Kubernetes, Slurm, SSH node pool, GPU, or storage task.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for disabled clouds, missing credentials, quota/capacity failures, Kubernetes context issues, Slurm partitions, SSH pools, storage mount errors, volume/PVC failures, and GPU catalog interpretation.

## Owns

- Infrastructure selection with `resources.infra`, `--infra`, `sky check`, `sky gpus list`, `sky gpus label`, and provider setup triage.
- Cloud/resource concepts: cloud, region, zone, accelerator, CPU, memory, instance type, spot, disk, local disk, ephemeral storage, disk tier, network tier, and labels.
- Kubernetes usage: `kubernetes`, `k8s`, `k8s/<context>`, kube contexts, namespaces, pod config, GPU labels, service accounts, ports, priorities, autoscaler hints, PVC-backed volumes, and multi-context routing.
- Slurm usage: `slurm`, `slurm/<cluster>`, `slurm/<cluster>/<partition>`, partition/GPU/resource mapping, Pyxis/FUSE support, and scheduler-specific symptoms.
- SSH node pools: `ssh`, `ssh/<pool>`, node-pool setup expectations, host volumes, and Kubernetes-compatible implementation details.
- Data surfaces: `workdir`, `file_mounts`, SkyPilot `Storage` objects, `MOUNT`, `COPY`, `MOUNT_CACHED`, cloud object-store backends, `sky storage`, `sky volumes`, persistent volumes, ephemeral volumes, and mount-mode troubleshooting.
- Safe credential triage that explains which command to run locally without asking the user to paste secrets or credentials.

## Route Elsewhere

- Task YAML syntax, `resources`, `file_mounts`, `volumes`, `envs`, and `secrets` field construction belongs to [../task-yaml/SKILL.md](../task-yaml/SKILL.md).
- Interactive cluster launch, status, logs, queue, stop/start/down, autostop, and cleanup belongs to [../cluster-operations/SKILL.md](../cluster-operations/SKILL.md).
- Managed jobs, recovery, queues, pools, and job logs belongs to [../managed-jobs/SKILL.md](../managed-jobs/SKILL.md).
- SkyServe service YAML operations, replicas, readiness, updates, and serving logs belongs to [../serving/SKILL.md](../serving/SKILL.md).
- Python SDK request IDs, API server login/status, dashboard, and remote server compatibility belongs to [../sdk-api-server/SKILL.md](../sdk-api-server/SKILL.md).
- Repository source changes, tests, formatting, and contribution workflow belongs to [../repo-development/SKILL.md](../repo-development/SKILL.md).

## Safe Preflight

Run the bundled checklist helper to plan what the user should verify locally:

```bash
python sub-skills/infrastructure-storage/scripts/resource_checklist.py \
  --cloud k8s --gpu H100:1 --storage volume --include-triage
```

The helper prints checks and SkyPilot commands only. It does not import SkyPilot, read credentials, inspect kubeconfig, contact cloud APIs, or mutate infrastructure.

## Operating Principles

- Prefer requirements over provider pins: ask for accelerator, CPU, memory, disk, and storage intent first; pin `--infra`, region, zone, instance type, Kubernetes context, Slurm partition, or SSH pool only when the user has a concrete placement or compliance requirement.
- Use `sky check <infra>` for credential/config readiness, `sky gpus list` for catalog and availability, and `sky launch --dryrun` for optimizer planning; do not parse pricing tables manually to choose the cheapest region.
- Separate authentication from capacity: credential and disabled-cloud errors are fixed with provider setup, while quota/capacity/stock errors are fixed by changing resource requirements, failover options, region/zone pins, or cloud choices.
- Treat object-store storage, `file_mounts`, and volumes as different tools: object stores are cross-region/cloud data surfaces, file mounts sync paths into a cluster, and volumes are high-performance provider/Kubernetes/RunPod-backed storage with lifecycle rules.
- Never ask the user to paste secrets, tokens, kubeconfigs, SSH private keys, or full cloud credential files; ask them to run local checks and share redacted error categories instead.
