---
name: setup-and-cli
description: "Install and inspect FedML, then operate the FedML CLI for login,
  devices, runs, clusters, storage, network diagnostics, and environment
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent_skill: "fedml"
license: Apache 2.0
---

# FedML Setup and CLI

Use this sub-skill for package installation, import repair, CLI discovery, account login/logout, device binding, run/cluster inspection, storage operations, backend network diagnostics, and environment snapshots.

## Do not use this for

- Building or launching job packages: use `../launch-and-packaging/SKILL.md`.
- Training loop implementation: use `../distributed-training/SKILL.md`.
- Federated-learning algorithm/workflow setup: use `../federated-learning/SKILL.md`.
- Model cards and serving endpoints: use `../model-serving/SKILL.md`.
- Workflow DAG composition: use `../workflow-orchestration/SKILL.md`.

## Setup path

1. Read `../../references/installation.md`.
2. Install with `pip install fedml` or `pip install -e python` from a source checkout.
3. Run the offline smoke check from the root skill directory:

   ```bash
   python scripts/check_install.py
   ```

4. If the import fails, read `../../references/troubleshooting.md#import-and-dependency-failures`.

## CLI discovery path

Use only help/version commands until the user approves remote side effects:

```bash
fedml --help
fedml version
fedml login --help
fedml run --help
fedml cluster --help
fedml storage --help
fedml network --help
fedml env --help
```

Important repo-specific command facts:

- Connectivity diagnostics are under `fedml network`, not `fedml diagnosis`.
- The current CLI root does not expose `fedml jobs`; use `fedml launch` and `fedml run` instead.

## Account and platform operations

Before running any command that changes remote state:

1. Confirm the target backend version (`release`, `test`, `dev`, or `local`).
2. Confirm the API key/source of credentials.
3. Confirm whether remote state changes are allowed.

Typical commands:

```bash
fedml login <api-key>
fedml logout
fedml device bind --help
fedml cluster list
fedml run list
fedml run status --help
fedml run logs --help
fedml storage list --help
```

Destructive commands such as `cluster stop`, `cluster kill`, `run stop`, `storage delete`, and `logout` require explicit approval.

## Python API equivalents

Read `../../references/api-reference.md#public-fedmlapi-helpers` when converting CLI work into Python. The usual setup/inspection APIs are:

- `fedml.api.fedml_login(api_key)`
- `fedml.api.run_list(...)`, `run_status(...)`, `run_logs(...)`, `run_stop(...)`
- `fedml.api.cluster_list(...)`, `cluster_status(...)`, `cluster_start/stop/kill/autostop(...)`
- `fedml.api.upload(...)`, `download(...)`, `list_storage_objects(...)`, `get_storage_metadata(...)`

## Exit criteria

A setup/CLI task is complete when the correct target environment is active, `import fedml` works, offline help/version checks pass, and any remote operation has a clear credential/side-effect decision recorded.
