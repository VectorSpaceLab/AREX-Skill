# Remote Workflows

Use this reference to choose a DVC remote pattern, write safe configuration commands, and separate no-network validation from real data transfer. The commands assume the `dvc` console script resolves to `dvc.cli:main` and the installed package is named `dvc`.

## Decision Matrix

| Need | Remote or command pattern | Safe validation | Network boundary |
| --- | --- | --- | --- |
| Share data through a local directory, external disk, or local test fixture | `dvc remote add -d localremote /abs/or/relative/path` | `dvc remote list`, `dvc config --list --show-origin`, `dvc status -c -r localremote` | Local filesystem only, but `push/pull/fetch/gc` still mutates data. |
| Inspect or import plain HTTP(S) data | `dvc get-url https://...`, `dvc import-url https://...` | `dvc import-url --help`, `dvc get-url --help`, config-only review | HTTP(S) commands contact network when executed. |
| Store data in S3, Google Cloud Storage, Azure Blob, OSS, SSH, HDFS, WebDAV, or WebHDFS | `dvc remote add <name> <scheme>://...` plus backend-specific `remote modify` settings | `python scripts/check_remote_support.py --scheme <scheme>`, `dvc remote list`, `dvc config remote.<name>.url` | Real transfer and auth occur in `push/pull/fetch/status -c/gc -c/import-url`. |
| Reference one configured remote from another | `dvc remote add derived remote://base/path` | `dvc remote list`, inspect base remote config | Resolution inherits base settings and may contact the base backend later. |
| Download tracked data from another DVC/Git repo | `dvc get`, `dvc get --show-url`, `dvc artifacts get` | `--show-url` can reveal the storage URL without downloading data | Downloading may clone/fetch and use the source repo default remote. |

## Local Filesystem Remote Recipe

Use this when the user asks for a safe example or a no-cloud workflow.

```bash
dvc remote add -d localremote /path/to/local-dvc-remote
dvc remote list
dvc config core.remote
dvc status -c -r localremote
```

Then explain transfer commands without running them unless the user explicitly approves local mutation:

```bash
dvc push -r localremote --run-cache
dvc fetch -r localremote --run-cache
dvc pull -r localremote --allow-missing
dvc gc --dry -r localremote
dvc gc -c -r localremote --dry
```

Notes:

- `dvc remote add -d` both creates `remote.<name>.url` and sets `core.remote` to that name.
- `dvc status -c` compares local cache to a remote; it may need to access the remote backend.
- `dvc pull` downloads cache and checks out workspace files; use `--force` only when overwriting workspace files is intended.
- `dvc fetch` fills cache without checkout. `dvc push` uploads cache. `--run-cache` includes run history for stages.

## HTTP and HTTPS URL Recipes

DVC includes HTTP(S) support as a core dependency in this checkout, but HTTP(S) operations still contact remote servers.

Read-only/no-network preparation:

```bash
dvc import-url --help
dvc get-url --help
dvc list-url --help
dvc config --list --show-origin
```

Examples to provide, not run without approval:

```bash
dvc import-url https://example.com/data.csv data/data.csv --no-exec
dvc get-url https://example.com/data.csv data.csv
dvc list-url https://example.com/data/ --recursive --level 2
```

Credential/config examples for HTTP(S) remotes:

```bash
dvc remote add httpdata https://example.com/dvc-cache
dvc remote modify --local httpdata user alice
dvc remote modify --local httpdata ask_password true
dvc remote modify httpdata ssl_verify true
```

Use `--local` for secrets and per-machine auth choices. Avoid putting passwords, tokens, or credential file paths in project config.

## S3, GS, Azure, OSS, SSH, HDFS, WebDAV, and WebHDFS Recipes

These backends require optional extras. Confirm availability with the bundled helper before suggesting a real transfer:

```bash
python scripts/check_remote_support.py --scheme s3
python scripts/check_remote_support.py --scheme gs
python scripts/check_remote_support.py --scheme azure
python scripts/check_remote_support.py --all
```

Narrow install guidance:

| URL scheme | DVC extra | Typical distribution/import checked by helper |
| --- | --- | --- |
| `s3://` | `dvc[s3]` | `dvc-s3` / `dvc_s3` |
| `gs://` | `dvc[gs]` | `dvc-gs` / `dvc_gs` |
| `azure://` | `dvc[azure]` | `dvc-azure` / `dvc_azure` |
| `oss://` | `dvc[oss]` | `dvc-oss` / `dvc_oss` |
| `ssh://` | `dvc[ssh]` or `dvc[ssh_gssapi]` for GSSAPI | `dvc-ssh` / `dvc_ssh` |
| `hdfs://` | `dvc[hdfs]` | `dvc-hdfs` / `dvc_hdfs` |
| `webdav://`, `webdavs://` | `dvc[webdav]` | `dvc-webdav` / `dvc_webdav` |
| `webhdfs://` | `dvc[webhdfs]` or `dvc[webhdfs_kerberos]` | `dvc-webhdfs` / `dvc_webhdfs` |

Configuration examples to adapt:

```bash
dvc remote add s3store s3://bucket/path
dvc remote modify --local s3store profile default
dvc remote modify s3store endpointurl https://s3.example.invalid

dvc remote add gsstore gs://bucket/path
dvc remote modify --local gsstore credentialpath /path/to/credentials.json

dvc remote add azurestore azure://container/path
dvc remote modify --local azurestore account_name <account>
dvc remote modify --local azurestore sas_token <token>

dvc remote add sshstore ssh://example.com/absolute/path
dvc remote modify --local sshstore user alice
dvc remote modify --local sshstore keyfile /path/to/key
```

Do not invent credential variable names or claim a provider backend is installed by default. If `RemoteMissingDepsError` names `s3`, the preferred advice is `pip install 'dvc[s3]'`, not `dvc[all]`.

## Data Transfer Commands

Common flags supported by `push`, `pull`, and `fetch`:

- `-j/--jobs <number>` controls transfer concurrency.
- `-r/--remote <name>` overrides the configured default remote.
- `-a/--all-branches`, `-T/--all-tags`, and `-A/--all-commits` expand Git revision scope.
- `-d/--with-deps` includes dependencies of specified targets.
- `-R/--recursive` covers subdirectories of the specified directory.
- `--run-cache` or `--no-run-cache` toggles run history transfer.
- `--glob` is available for target patterns; in `pull` it is hidden in help but supported by the command parser.

Additional command notes:

- `dvc pull` supports `--force` and `--allow-missing` because it may update the workspace after fetching cache.
- `dvc fetch` supports `--max-size <bytes>` and repeated `--type metrics` or `--type plots` filters.
- `dvc status -c` compares local cache with remote storage; use `--json` when a script needs machine-readable status.
- If no `-r` is provided and no `core.remote` exists, data sync commands warn that no remote was provided and no default remote is set.

## Import and URL Transfer Interactions

These commands belong here only when the user asks about remote or URL transfer behavior:

```bash
dvc import-url <url> [out]
dvc import-url <url> [out] --no-exec
dvc import-url <url> [out] --no-download
dvc import-url <url> [out] --to-remote -r <remote>
dvc get <repo-url> <path> --show-url --remote <remote>
dvc get-url <url> [out] --fs-config key=value
dvc list-url <url> --recursive --level 2
dvc artifacts get <repo-url> <name> --show-url --remote <remote>
```

Important constraints:

- `dvc import-url --to-remote` cannot be combined with `--no-exec`, `--no-download`, or `--version-aware`.
- `dvc import-url --remote <name>` is valid only with `--to-remote`.
- Supported `import-url` examples include local paths, relative paths, Windows paths, HTTP(S), `s3://`, `gs://`, `hdfs://`, `ssh://`, and `remote://remote_name/path`.
- `--fs-config key=value` passes URL-specific filesystem config for `import-url`, `get-url`, and `list-url`; treat secrets in these values carefully.

## Garbage Collection and Cache Safety

Start with dry runs:

```bash
dvc gc --dry
dvc gc --dry --workspace
dvc gc --dry --all-branches --all-tags
dvc gc --dry --not-in-remote -r <remote>
dvc gc --dry -c -r <remote>
```

Explain before running:

- `dvc gc` removes local cache objects not needed by the selected workspace/revision scope.
- `dvc gc -c` also garbage-collects remote storage.
- `--not-in-remote` keeps local cache that is not present in the remote.
- `-p/--projects <paths>` protects data used by additional projects sharing the same cache.
- `-f/--force` skips confirmation prompts; avoid it unless the user explicitly wants noninteractive cleanup.
