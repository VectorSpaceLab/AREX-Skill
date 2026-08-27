---
name: remote
description: "Routes LabML remote-project setup, job orchestration, and
  distributed launch workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Remote

Use this subskill for `labml_remote`: project bootstrap, remote server setup,
rsync-based sync, job management, and distributed launch helpers.

## Use this when

- The task mentions `labml_remote`, `.remote/configs.yaml`, `.remote/exclude.txt`,
  `init`, `prepare`, `run`, `job-run`, `job-tail`, `job-kill`, or
  `helper-torch-launch`.
- The user wants to set up a remote machine, sync a project, run commands on a
  server, or launch distributed training jobs over SSH.

## Boundaries

Include:
- Remote-project configuration and bootstrap files.
- SSH/rsync command orchestration.
- Job creation, listing, tailing, killing, and syncing.
- Distributed launch helpers that build on the remote job system.

Exclude or route elsewhere:
- Client-side tracking and monitoring → `tracking`.
- Training-loop utilities and datasets → `helpers`.
- App backend and monitoring UI deployment → `server`.

## Read next

- `references/cli-reference.md` for the command set and options.
- `references/workflows.md` for the remote-project lifecycle and distributed
  launch recipe.
- `references/troubleshooting.md` for SSH, conda, rsync, and job-state issues.
- `scripts/remote_config_smoke.py` for a safe local init/configuration check.

## Typical routes

### Bootstrap a remote project
Choose this route for `labml_remote init`, the `.remote/` files, and the
initial server configuration.

### Prepare or sync a server
Choose this route for `prepare`, `setup`, `rsync`, and `update-packages`.

### Run or manage jobs
Choose this route for `run`, `job-run`, `job-list`, `job-tail`, and `job-kill`.

### Launch distributed training
Choose this route for `helper-torch-launch` and the environment variables that
assemble a multi-node training job.
