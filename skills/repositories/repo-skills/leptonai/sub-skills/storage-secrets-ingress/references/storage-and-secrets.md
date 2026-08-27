# Storage and secrets

This reference covers LeptonAI workspace file storage and workspace secrets. Treat every command here as a live workspace operation unless it is a `--help` command or a local syntax preflight.

## Storage command map

The file-storage Click group is available as `lep storage ...`; `lep file ...` is also registered as a hidden alias for the same command group. Use either spelling only after checking the user's preferred convention for the current project or script.

| Goal | CLI pattern | Important behavior | Confirmation needed? |
|---|---|---|---|
| Show workspace disk use | `lep storage du` | Prints total file-system usage in human-readable units. | Read-only, but still needs workspace auth. |
| List a storage path | `lep storage ls PATH [-fs FILE_SYSTEM]` | Checks that the remote path exists, then prints child entries and file/dir counts. | Read-only. |
| List dedicated file systems | `lep storage ls-file-system` | Shows file-system names and total usage bytes. | Read-only. |
| Create a directory | `lep storage mkdir PATH [-fs FILE_SYSTEM]` | Creates a remote directory under the selected file system. | Yes. |
| Upload a file | `lep storage upload LOCAL_PATH [REMOTE_PATH] [-fs FILE_SYSTEM]` | If `REMOTE_PATH` ends with `/`, the local basename is appended. Default remote path is `/`. | Yes: confirm source, destination, and overwrite expectations. |
| Upload with rsync | `lep storage upload LOCAL_PATH REMOTE_PATH --rsync [-r] [-p] [-ar N]` | For large files/directories. `--recursive`, `--progress`, and non-default `--auto-recover` are valid only with `--rsync`. Uses a cloud helper pod and can retry interrupted transfers. | Yes; also confirm helper availability and transfer size. |
| Download a file | `lep storage download REMOTE_PATH [LOCAL_PATH] [-fs FILE_SYSTEM]` | Remote target must be a file. Empty `LOCAL_PATH` uses the current directory plus the remote basename; a directory target appends the remote basename; parent directory must already exist. | Yes: confirm destination and overwrite risk. |
| Delete a file | `lep storage rm PATH [-fs FILE_SYSTEM]` | Rejects directories and tells the user to use `rmdir`; wildcards are not supported. | Yes; destructive. |
| Delete a directory | `lep storage rmdir PATH [-fs FILE_SYSTEM] [-r]` | Rejects files and tells the user to use `rm`. Without `-r`, the directory must be empty. Wildcards are not supported. | Yes; destructive, especially with `-r`. |

`-fs`/`--file-system` selects a named file system for workspaces with dedicated file-system support. When omitted, the API uses the package's default storage volume name.

## Safe transfer planning

For upload/download requests, build a plan before running anything:

1. Determine whether the user means a single file or a directory.
2. Normalize the remote path convention: storage API paths are remote POSIX-style paths; a trailing slash in upload means "place under this remote directory using the local basename".
3. For downloads, confirm whether the local target already exists or might be overwritten.
4. For large or recursive uploads, prefer the rsync form and explain that it depends on a workspace helper pod. Do not create or repair that helper unless the user authorizes cloud mutations.
5. Do not assume shell wildcards work with `rm` or `rmdir`; enumerate exact paths first.

Examples to present as plans, not to run without authorization:

```bash
# Read-only check before transferring
lep storage ls /datasets

# Upload one file to an explicit remote filename
lep storage upload ./manifest.json /datasets/manifest.json

# Upload into a remote directory using the local basename
lep storage upload ./manifest.json /datasets/

# Recursive rsync upload with progress and three recovery attempts
lep storage upload ./dataset /datasets/dataset --rsync --recursive --progress --auto-recover 3

# Download to an existing local directory
lep storage download /datasets/manifest.json ./downloads/
```

## Storage API surface

For Python automation, `APIClient().storage` exposes the same workspace storage surface. These methods perform live authenticated HTTP calls when invoked:

| API method | Purpose |
|---|---|
| `list_storage()` | List file systems. |
| `total_file_system_usage_bytes()` | Return a file-system object containing total usage bytes. |
| `check_exists(path, file_system=None)` | `HEAD` check for a remote file or directory. |
| `get_dir(path, file_system=None)` | List a remote directory as `DirInfo` objects (`name`, `type`, `path`). |
| `get_file_type(path, file_system=None)` | Return `"file"`, `"dir"`, or `None` by checking the parent directory. |
| `create_dir(path, file_system=None)` | Create a remote directory. |
| `create_file(local_path, remote_path, file_system=None)` | Upload a local file as multipart data. |
| `get_file(remote_path, local_path, file_system=None)` | Stream-download a remote file to a local file. |
| `delete_file_or_dir(path, file_system=None, removeall=False)` | Delete a file or directory; `removeall=True` corresponds to recursive directory removal. |

Keep SDK examples as dry plans unless the user explicitly approves live workspace access.

## Secret command map

Secrets are workspace-scoped named values. Values are write-only from the CLI user's perspective: `lep secret list` prints metadata but not the secret value.

| Goal | CLI pattern | Important behavior | Confirmation needed? |
|---|---|---|---|
| Create one secret | `lep secret create -n NAME -v VALUE` | Creates a private secret by default. Do not echo the value in chat or logs. | Yes, because it writes secret material to the workspace. |
| Create multiple secrets | `lep secret create -n NAME1 -v VALUE1 -n NAME2 -v VALUE2` | The number of names must match the number of values. The command checks for existing names and asks the user to remove conflicting secrets first. | Yes. |
| Create a public-key secret | `lep secret create -n NAME -v VALUE --public-key` | Sets secret visibility to public. Confirm the user's intent because visibility changes who can use the secret. | Yes. |
| List secrets | `lep secret list` | Shows name, tags, owner, and visibility; values remain hidden. | Read-only. |
| Remove a secret | `lep secret remove -n NAME` | If the name does not exist, the CLI prints a warning and returns without deleting anything. | Yes; destructive. |

Secret names that collide with platform-reserved environment names are rejected. If the user needs to pass a secret to a workload, prefer a secret reference (`--secret NAME=SECRET_NAME` or `--secret SECRET_NAME`) over literal values in `--env`.

## Secret API surface

`APIClient().secret` provides:

| API method | Purpose |
|---|---|
| `list_all()` | Return all secret metadata as `SecretItem` objects. |
| `create([SecretItem(...)])` | Create one or more secrets. The payload contains values, so keep it out of logs. |
| `delete(name)` | Delete a named secret. |

## Redaction rules

- Never paste real secret values or literal access tokens into a command transcript, issue, report, or generated script.
- When showing a secret plan, display only secret names and whether a value is provided.
- For `--env`, assume values may be sensitive; show key names and redacted value placeholders unless the user explicitly asks to display non-sensitive values.
- For transfers, paths can also reveal data names. Confirm whether path names are safe to display before sharing logs externally.
