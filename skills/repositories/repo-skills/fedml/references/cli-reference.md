# FedML CLI Reference

## Purpose

Read this for the command surface exposed by `fedml`. The command names and options below were verified from the installed package help output.

## Root commands

| Command | What it does | Notes |
| --- | --- | --- |
| `fedml login` | Login to the FedML Nexus AI platform | supports `-v/--version`, `-c/--compute_node`, `-s/--server`, `-p/--provider`, `-dpn/--deploy_worker_num`, `-lp/--local_on_premise_platform`, `-lpp/--local_on_premise_platform_port` |
| `fedml logout` | Logout from the platform | supports `-v/--version`, `-c/--computing`, `-s/--server` |
| `fedml launch` | Launch a job from a job YAML | supports `-k/--api_key`, `-g/--group`, `-v/--version`, `-c/--cluster`, `-lp/--local_on_premise_platform`, `-lpp/--local_on_premise_platform_port` |
| `fedml build` | Build client/server packages | supports `-pf/--platform`, `-t/--type`, `-sf/--source_folder`, `-ep/--entry_point`, `-cf/--config_folder`, `-df/--dest_folder`, `-ig/--ignore` |
| `fedml run` | Inspect and stop runs | subcommands: `list`, `status`, `logs`, `stop` |
| `fedml cluster` | Manage clusters | subcommands: `start`, `startall`, `stop`, `stopall`, `kill`, `killall`, `list`, `status`, `autostop` |
| `fedml device` | Bind/unbind devices and show GPU resource types | subcommands: `bind`, `unbind`, `gpu-type` |
| `fedml model` | Manage model cards and inference endpoints | subcommands: `create`, `push`, `deploy`, `run`, `pull`, `list`, `delete`, `package` |
| `fedml train` | Build training packages | subcommand: `build` |
| `fedml federate` | Build federated-learning packages | subcommand: `build` |
| `fedml storage` | Upload, list, inspect, download, and delete stored objects | subcommands: `upload`, `list`, `get-user-metadata`, `get-metadata`, `download`, `delete` |
| `fedml network` | Check backend connectivity | this is the actual command name in the current CLI, not `diagnosis` |
| `fedml env` | Show environment and network info | supports `-v/--version` |
| `fedml version` | Print package version | no extra options |

## Important command notes

### Login / logout

- `login` and `logout` are the account/device entry points.
- `login` can act as compute node, on-prem server, or GPU provider.
- These commands typically require an API key or user id and may touch remote state.

### Launch and build

- `build` packages a source folder plus config folder into client or server artifacts.
- `launch` submits a YAML-defined job to the platform and can target a named cluster.
- The current CLI does not expose a top-level `jobs` command, even though older docs mention one.

### Runs / clusters / devices

- `run` is the main inspection/management group for already launched jobs.
- `cluster` manages named compute clusters and can autostop them.
- `device` is for binding/unbinding and querying GPU resource types.

### Model management

- `model create` creates a local model card.
- `model deploy` supports local, on-prem, and GPU-cloud deployment.
- `model run` is the request path for inference endpoints.

### Storage

- `storage upload` and `storage download` are the public data/object-store helpers.
- These commands are network-bound and may require API credentials.

### Diagnostics

- Use `fedml network` for connectivity probes.
- Use `fedml env` for a wider environment snapshot, including hardware and networking.

## Where to go next

- `references/api-reference.md` for Python APIs.
- `references/workflows.md` for workflow selection guidance.
- `references/troubleshooting.md` for common CLI and environment failures.
