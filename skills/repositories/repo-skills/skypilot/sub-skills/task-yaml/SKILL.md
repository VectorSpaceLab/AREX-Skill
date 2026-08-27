---
name: task-yaml
description: "Author, validate, troubleshoot, and adapt SkyPilot task and
  service YAMLs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SkyPilot Task YAML

Use this sub-skill when the user needs to write, review, convert, or debug a SkyPilot task YAML, a SkyServe YAML's task portion, or Python code that constructs `sky.Task` and `sky.Resources` from YAML-compatible config.

## Start Here

1. Read `references/yaml-reference.md` for accepted top-level fields, resource forms, service YAML fields, Python construction APIs, and safe validation flow.
2. Use `scripts/validate_task_or_service_yaml.py` for parser-only validation when SkyPilot is installed; it does not launch clusters, contact clouds, or write resources.
3. Read `references/troubleshooting.md` when validation fails or when YAML behavior is ambiguous.

## Owns

- Task fields: `name`, `workdir`, `num_nodes`, `resources`, `envs`, `secrets`, `api_server_access`, `volumes`, `file_mounts`, `setup`, `run`, and `config`.
- Resource fields: `infra`, `accelerators`, `cpus`, `memory`, `instance_type`, `use_spot`, `disk_size`, `ephemeral_storage`, `disk_tier`, `network_tier`, `ports`, `labels`, `any_of`, `ordered`, `autostop`, `job_recovery`, `priority`, and `priority_class`.
- Storage/file-mount basics: local path copies, cloud object-store mounts, `MOUNT`, `COPY`, `MOUNT_CACHED`, mount-cached presets, and Kubernetes volume references.
- Python parser construction with `sky.Task.from_yaml()`, `sky.Task.from_yaml_config()`, `sky.Task.from_yaml_str()`, and `sky.Resources(...)`.
- Service YAML field validation for the `service:` section and service-spec fragments, then routing runtime SkyServe operations elsewhere.

## Route Elsewhere

- Launching, executing, stopping, status, logs, autostop operations, and cleanup belong to `../cluster-operations/SKILL.md`.
- Managed job lifecycle, queues, recovery behavior, job pools, and job logs belong to `../managed-jobs/SKILL.md`.
- SkyServe operations, service updates, production rollout, and replica debugging belong to `../serving/SKILL.md`.
- Credential triage, provider setup, Kubernetes/Slurm/SSH details, GPU availability, and deep storage/provider failures belong to `../infrastructure-storage/SKILL.md`.
- SDK request handling, API server lifecycle, and remote server compatibility belong to `../sdk-api-server/SKILL.md`.
- Source edits, tests, formatting, and contribution rules belong to `../repo-development/SKILL.md`.

## Safe Validation

Run the bundled parser helper from this sub-skill directory or with an explicit path:

```bash
python scripts/validate_task_or_service_yaml.py --kind auto path/to/task.yaml
```

Use `--kind task` for normal task YAMLs and `--kind service` for SkyServe YAMLs or service-spec fragments. The helper imports SkyPilot parser APIs only; it is not a dry run, optimizer call, or credential check.
