# Remote Configuration

## Purpose

Read this when you need to create or inspect `.remote/configs.yaml` and
`.remote/exclude.txt`.

## Config object shape

`labml_remote.configs.Configs` loads a dictionary with these common keys:

| Key | Meaning |
| --- | --- |
| `name` | Project name used as the remote folder name. |
| `servers` | Mapping of server IDs to server configuration objects. |
| `scripts_folder` | Local folder that stores generated helper scripts. |
| `logs_folder` | Local folder for rsync and command logs. |
| `jobs_folder` | Local folder for background job metadata. |
| `exclude_file` | Path to the rsync exclude file. |
| `remote_scripts_folder_name` | Folder name used on the remote host for helper scripts. |
| `remote_jobs_folder_name` | Folder name used on the remote host for job outputs. |

Each server entry becomes a `ServerConfig` with:

| Key | Meaning |
| --- | --- |
| `hostname` | SSH host name or IP. Required. |
| `username` | SSH username. Defaults to `ubuntu`. |
| `password` | Optional password. |
| `private_key` | Optional private key file path. |
| extra keys | Stored in `properties` for custom use. |

## Generated default project

`create_default_project(path)` creates or updates:

- `path/.remote/configs.yaml`
- `path/.remote/exclude.txt`

The default exclude file skips:

- `.remote`
- `.git`
- `__pycache__`
- `.ipynb_checkpoints`
- `logs`
- `.DS_Store`
- `.*.swp`
- `*.egg-info/`
- `.idea`

## When to read this file

- You need to know where a project stores generated sync artifacts.
- You want to validate a `.remote/configs.yaml` before running remote commands.
- You need to understand the default exclude list or override it safely.
