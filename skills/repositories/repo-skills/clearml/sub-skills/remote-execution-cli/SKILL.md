---
name: remote-execution-cli
description: "Configure ClearML and build safe remote execution commands or SDK
  launch flows with clearml-task, clearml-init, clearml-debug, Task.create,
  Task.clone, Task.enqueue, and Task.execute_remotely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearML Remote Execution CLI

Use this sub-skill when an agent needs to configure ClearML, launch code on a `clearml-agent`, create or clone a remote task, enqueue an existing task, import an offline session, or diagnose why a `clearml-task`/remote execution request is not running.

## Start Here

1. Confirm the user has a ClearML server target and credentials configured via environment variables or a ClearML config file; use [`scripts/validate_clearml_environment.py`](scripts/validate_clearml_environment.py) for a read-only signal check that does not print secret values.
2. Decide whether the launch is CLI-first (`clearml-task`) or SDK-first (`Task.create`, `Task.clone`, `Task.enqueue`, `Task.execute_remotely`). Use CLI-first for CI/CD and command construction; use SDK-first when code already owns a `Task` object or needs programmatic clone/enqueue behavior.
3. Build commands with [`scripts/build_clearml_task_command.py`](scripts/build_clearml_task_command.py), which validates incompatible options and prints a shell-safe command without contacting a ClearML server.
4. Use [`references/cli-reference.md`](references/cli-reference.md) for command flags and templates, [`references/workflows.md`](references/workflows.md) for launch patterns, and [`references/troubleshooting.md`](references/troubleshooting.md) for failure triage.

## Route Related Work

- For metrics, plots, logs, models, or artifacts inside the launched script, use `../experiment-tracking/SKILL.md`.
- For `clearml-data`, `Dataset`, `StorageManager`, or dataset storage workflows, use `../data-storage/SKILL.md`.
- For pipelines, pipeline CLI flags, schedulers, services, or HPO, use `../automation-pipelines/SKILL.md`.

## Safe Operating Rules

- Do not run `clearml-task`, `clearml-init`, `clearml-debug token`, or SDK launch/enqueue code unless the user explicitly wants side effects against a ClearML server.
- Prefer producing a reviewed command and validation checklist; remote execution requires credentials, network access, and a polling `clearml-agent` on the selected queue.
- Never echo ClearML secret values in instructions, logs, or generated scripts. Redact or report presence only.
- Treat repository, Docker image, package, requirements, queue, and output URI as deployment decisions; ask when any are missing or ambiguous.
- If no `--queue` is provided, `clearml-task` creates a draft task but does not launch it.

## Minimum Launch Checklist

- `--project` and `--name` are set unless using `--import-offline-session`.
- Exactly one entry style is chosen: `--script`, `--module`, `--base-task-id`, or `--import-offline-session`.
- Code source is explicit: `--repo` for a remote repository, `--folder` for a local git checkout, or `--skip-repo-detection` when source capture is intentionally disabled.
- Environment is explicit enough for the agent: `--requirements`, `--packages`, `--force-no-requirements`, or `--skip-python-env-install`.
- Queue name matches a live ClearML agent pool; otherwise the task remains queued.
- Use `--skip-task-init` only when the script already calls `Task.init()` or should not be patched by `clearml-task`.
