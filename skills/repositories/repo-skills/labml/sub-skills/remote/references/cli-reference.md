# Remote CLI Reference

## Purpose

Read this for the `labml_remote` command set and the file layout it expects in a
project directory.

## Command summary

| Command | Purpose | Notable options |
| --- | --- | --- |
| `labml_remote init` | Create `.remote/configs.yaml` and `.remote/exclude.txt` for a project. | Interactive prompts for project name, host, user, and private key. |
| `labml_remote setup` | Install Python on the server with conda. | `--server`, `--show-output` |
| `labml_remote rsync` | Sync the project contents to one or more servers. | `--server`, `--show-output` |
| `labml_remote update-packages` | Update pip packages on the server. | `--server`, `--show-output` |
| `labml_remote prepare` | Run setup, sync, and package update in one pass. | `--server`, `--show-output` |
| `labml_remote run` | Run a shell command on a server. | `--server`, `--cmd`, `--env`, `--silent` |
| `labml_remote job-run` | Start a background job. | `--server`, `--cmd`, `--env`, `--tag` |
| `labml_remote job-rsync` | Sync job outputs from the server. | `--server`, `--delay`, `--show-output` |
| `labml_remote job-list` | List tracked jobs. | `--rsync`, `--stopped`, `--hidden`, `--tag` |
| `labml_remote job-tail` | Tail a tracked job. | `--job`, `--tag`, `--delay` |
| `labml_remote job-kill` | Kill tracked jobs. | `--job`, `--tag`, `--signal` |
| `labml_remote helper-torch-launch` | Launch distributed PyTorch jobs. | `--cmd/--python-cmd`, `--nproc-per-node`, `--use-env`, `--master-port`, `--env`, `--tag` |

## Project files

- `.remote/configs.yaml` stores project and server settings.
- `.remote/exclude.txt` lists paths that should not be rsynced.
- `.remote/scripts/` is where the generated helper scripts live inside the
  project.
- `.remote/logs/` and `.remote/jobs/` store local sync artifacts.

## CLI behavior notes

- `labml_remote` prints a warning when no servers are configured.
- `helper-torch-launch` adds the standard distributed environment variables for
  each job, including `RUN_UUID`, `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`,
  `NODE_RANK`, `RANK`, and `LOCAL_RANK`.
- `job-*` commands operate on the locally tracked job metadata and the synced
  output files.
