---
name: cli-cloud
description: "Routes AXLearn GCP CLI, bundling, launch, VM, bastion, Dataflow,
  logs, and auth workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cli-cloud

Use this sub-skill for AXLearn's cloud command tree and GCP-facing operations.

Typical triggers:

- `axlearn gcp config`, `activate`, `cleanup`, or `get`.
- `axlearn gcp bundle` for tar/docker bundling.
- `axlearn gcp launch`, `vm`, `bastion`, `dataflow`, `logs`, or `auth`.
- Questions about the `.axlearn/axlearn.default.config` and `.axlearn/.axlearn.config` files.
- TPU/GKE/Dataflow launch workflows or Cloud Logging log retrieval.

If the task is only about trainer config mechanics or fake-data smoke checks, use `../training-core/` first.
If the task is about the model that will run on the cloud, jump to the relevant domain sub-skill.

## What to read

- `references/cli-reference.md` for the command tree and config-file behavior.
- `references/gcp-config-template.md` for the distilled TOML config shape.
- `references/troubleshooting.md` for GCP auth, config, and log-view failures.
- `scripts/inspect_gcp_cli.py` for a safe command-tree probe.

## Core cloud workflows

### 1) Inspect the command tree

The CLI is self-documenting. Use the bundled helper or run `axlearn gcp --help` to inspect subcommands and flags.

### 2) Activate a GCP config

The GCP config namespace is stored in the repo or home config file. List available entries first, then activate one by label.

### 3) Bundle the local code

Use `bundle` when you need to package the current checkout into a tarball or Docker image for launch.

### 4) Launch or monitor jobs

Use `launch`, `vm`, or `bastion` to submit a job and to manage its runtime. Use `dataflow` for Dataflow jobs and `logs` for Cloud Logging log access.

## Decision points

- Choose `config` when the task is about project activation or CLI defaults.
- Choose `bundle` when the task is about packaging the current checkout.
- Choose `launch` or `vm` when the task is about running a command remotely.
- Choose `bastion` when the task is about job scheduling and quota management.
- Choose `dataflow` when the task is about Beam/Dataflow runner setup.
- Choose `logs` when the task is about log inspection rather than job execution.
- Do not route trainer/model-specific questions here unless the question is really about how the cloud launcher wraps them.
