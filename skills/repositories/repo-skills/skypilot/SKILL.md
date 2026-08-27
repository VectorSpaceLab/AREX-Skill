---
name: skypilot
description: "Use SkyPilot to run, manage, and scale AI workloads across clouds,
  Kubernetes, Slurm, SSH node pools, managed jobs, SkyServe services, storage
  mounts, and the Python SDK."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SkyPilot

SkyPilot is a unified interface for launching, managing, and scaling AI workloads across cloud VMs, Kubernetes, Slurm, SSH node pools, and managed service deployments. Use this repo skill when a user asks for SkyPilot task YAMLs, `sky` CLI commands, Python SDK flows, managed jobs, SkyServe, storage mounts, cloud/resource selection, or SkyPilot source-code changes.

## Bootstrap

1. Confirm SkyPilot is installed and the CLI is reachable:

   ```bash
   python scripts/check_skypilot_env.py --check-cli
   ```

2. For live SkyPilot use, check API server connectivity:

   ```bash
   sky api info
   ```

3. For cloud/provider readiness, check credentials only when the user intends to launch or query resources:

   ```bash
   sky check -o json
   ```

4. Read `references/troubleshooting.md` if install, import, API server, credentials, optional extras, or command-output issues appear.

## Route By Task

| User goal | Read |
| --- | --- |
| Write, review, convert, or validate SkyPilot task YAMLs, service YAML task fields, resources, mounts, envs, secrets, storage, or `sky.Task`/`sky.Resources` config. | `sub-skills/task-yaml/SKILL.md` |
| Launch/reuse interactive clusters, run `sky exec`, inspect status/logs/queues, manage autostop, stop/start/down, or plan safe cluster CLI commands. | `sub-skills/cluster-operations/SKILL.md` |
| Submit long-running training or batch workloads with `sky jobs`, managed spot recovery, job logs/queue/cancel, job groups, or job pools. | `sub-skills/managed-jobs/SKILL.md` |
| Deploy or debug SkyServe services, service YAMLs, readiness probes, replicas, autoscaling, load balancing, updates, logs, or LLM serving recipes. | `sub-skills/serving/SKILL.md` |
| Configure clouds, Kubernetes, Slurm, SSH node pools, GPU/resource selection, `sky check`, `sky gpus`, workspaces, object storage, file mounts, or volumes. | `sub-skills/infrastructure-storage/SKILL.md` |
| Use the Python SDK, async SDK, request IDs, `sky.get()`, API server lifecycle, remote server login, dashboard/API deployment, or compatibility checks. | `sub-skills/sdk-api-server/SKILL.md` |
| Modify the SkyPilot repository, choose focused tests, run formatting/linting, regenerate protobufs, rebuild dashboard assets, or prepare PR `Tested:` notes. | `sub-skills/repo-development/SKILL.md` |

## Core Decision Rules

- Prefer SkyPilot's optimizer: specify resources and constraints, then let SkyPilot choose cloud/region/zone unless the user explicitly pins infrastructure.
- Use `sky launch --dryrun` before expensive interactive launches; use parser-only validators for YAML checks when cloud access is unnecessary.
- Use `sky jobs launch` for unattended long-running work that should survive spot preemptions and capacity failures.
- Use SkyServe for service endpoints and replica management; test the underlying HTTP server with a simpler task or cluster workflow when startup is uncertain.
- Use structured output (`-o json`) for automation-friendly `status`, `queue`, `jobs queue`, `check`, and related inspection commands when supported.
- Keep secrets in `secrets`, `--secret`, or secret files; do not embed credentials in shared YAML, prompts, logs, or scripts.
- Treat smoke tests, live launches, serving deployments, pool creation, and provider checks as resource/credential-bound unless the user explicitly authorizes them.

## Bundled Helpers

- `scripts/check_skypilot_env.py` verifies package importability, version, optional CLI help, and common missing-install symptoms without launching resources.
- `scripts/inspect_cli_groups.py` prints safe help summaries for selected `sky` command groups without running launches, jobs, or services.
- Sub-skill scripts provide parser-only validators, command builders, SDK inspectors, resource checklists, and repo-maintenance sanity checks.

## Evidence And Staleness

- Read `references/repo-provenance.md` before deciding whether this skill matches a current SkyPilot checkout.
- Read `references/evidence-map.md` to understand the source areas distilled into this self-contained skill.
- If the current checkout commit, major public APIs, CLI flags, YAML schema, docs, examples, or dependencies changed, refresh this skill before relying on detailed guidance.
