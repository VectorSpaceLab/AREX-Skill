---
name: deployment-orchestration
description: "Guides Metaflow remote compute, production schedulers, projects,
  schedules, events, secrets, resources, and safe deployment preflight
  decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment Orchestration

Use this sub-skill when a task involves AWS Batch, Kubernetes, Argo Workflows, AWS Step Functions, Airflow, `@resources`, `@parallel`, `@pytorch_parallel`, `@schedule`, `@trigger`, `@trigger_on_finish`, `@project`, `@secrets`, or production deployment commands.

## Quick Route

- Read [`references/remote-compute.md`](references/remote-compute.md) for Batch, Kubernetes, resources, parallelism, GPUs, and remote task prerequisites.
- Read [`references/production-schedulers.md`](references/production-schedulers.md) for Step Functions, Argo Workflows, Airflow, scheduler CLIs, and `Deployer` bridge decisions.
- Read [`references/events-and-projects.md`](references/events-and-projects.md) for projects, schedules, triggers, namespaced events, and secrets.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for datastore requirements, unsupported decorator combinations, timeout/resource errors, and credential/service blocks.
- Run [`scripts/deployment_preflight.py`](scripts/deployment_preflight.py) for read-only optional import and environment-variable diagnostics.

## Safety Boundary

Compile/help checks can be safe; real deploy, trigger, terminate, delete, kill, or cloud list operations can contact services or mutate remote state. Do not run those commands without explicit user approval and verified credentials/configuration.

## Boundaries

- Local flow syntax belongs in [`../flow-authoring/SKILL.md`](../flow-authoring/SKILL.md).
- Per-step dependency environments belong in [`../dependency-environments/SKILL.md`](../dependency-environments/SKILL.md).
- Programmatic `Runner`/`Deployer` object basics belong in [`../runner-and-programmatic/SKILL.md`](../runner-and-programmatic/SKILL.md).
