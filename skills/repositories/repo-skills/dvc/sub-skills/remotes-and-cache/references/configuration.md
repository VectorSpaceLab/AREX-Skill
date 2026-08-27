# Remote and Cache Configuration

Use this reference when editing DVC config for remotes, default remote selection, cache directory, cache link type, or protected workspace files.

## Config Levels

DVC commands that edit config accept one of these mutually exclusive levels:

| Level flag | Stored in | Use for |
| --- | --- | --- |
| `--project` | `.dvc/config` | Shareable repo configuration such as remote names and non-secret URLs. |
| `--local` | `.dvc/config.local` | Credentials, user-specific paths, provider profiles, tokens, key files, and local cache paths. |
| `--global` | User-level DVC config | Defaults reused across many repos on one machine. |
| `--system` | System-level DVC config | Admin-managed defaults. |

If no level is specified inside a DVC repo, commands read merged levels. Writes typically target repo/project config unless the command or user chooses another level.

Safe inspection commands:

```bash
dvc config --list
dvc config --list --show-origin
dvc config core.remote
dvc remote list
dvc remote default
```

`--show-origin` is read-only and helps explain which config file is shadowing another setting.

## Remote Commands

Remote names are normalized to lowercase by the command implementation.

```bash
dvc remote add [-d|--default] [-f|--force] [--project|--local|--global|--system] <name> <url>
dvc remote modify [--local|--project|--global|--system] <name> <option> [value]
dvc remote modify <name> <option> --unset
dvc remote default [<name>]
dvc remote default --unset
dvc remote list
dvc remote remove <name>
dvc remote rename <name> <new>
```

Behavior to remember:

- `remote add -d` sets `core.remote` to the added remote.
- `remote add` refuses to overwrite an existing remote unless `-f/--force` is used.
- `remote default <name>` fails unless the remote exists in the selected or merged config.
- `remote remove` deletes matching default remote references up to the edited config level.
- `remote rename` updates `core.remote` references when the renamed remote was default.

Equivalent direct config forms:

```bash
dvc config remote.<name>.url <url>
dvc config remote.<name>.<option> <value>
dvc config remote.<name>.<option> --unset
dvc config core.remote <name>
```

Prefer `dvc remote ...` for normal user workflows because it validates remote existence and default behavior more directly.

## URL Schemes and Remote References

DVC validates `remote.<name>.url` by URL scheme. Practical schemes include:

- Local paths and empty-scheme paths for filesystem remotes.
- `http://` and `https://` for HTTP(S) remotes.
- `s3://`, `gs://`, `azure://`, `oss://`, `ssh://`, `hdfs://`, `webdav://`, `webdavs://`, and `webhdfs://` for optional backend remotes.
- `remote://base/path` to derive a remote from another configured remote and merge/override its settings.

For `remote://base/path`, DVC resolves the base remote first, then appends the relative path using that backend's separator. Settings on the derived remote override inherited settings.

## Practical Remote Options

Common options available for all or many remote types:

| Option | Applies to | Purpose |
| --- | --- | --- |
| `url` | all remotes | Backend URL or path. Required. |
| `jobs` | all remotes | Transfer concurrency for that remote. |
| `checksum_jobs` | all remotes | Checksum concurrency; falls back to `core.checksum_jobs` when omitted. |
| `version_aware` | all remotes | Enables cloud version-aware behavior where supported. |
| `verify` | local and most backends | Enables backend verification where supported. |
| `user`, `password`, `ask_password` | HTTP, SSH, WebDAV, WebHDFS | Authentication. Keep secrets local. |
| `ssl_verify` | HTTP(S), S3, WebDAV, WebHDFS | Boolean or certificate path depending on backend. |
| `profile`, `credentialpath`, `endpointurl` | S3/GS | Provider profile, credentials, and custom endpoints. |
| `account_name`, `account_key`, `sas_token`, `client_id`, `client_secret` | Azure | Azure identity and token configuration. |
| `keyfile`, `passphrase`, `ask_passphrase`, `port`, `gss_auth` | SSH | SSH authentication and connection options. |

When a value is a secret or a machine path, use `--local`:

```bash
dvc remote modify --local s3store profile default
dvc remote modify --local sshstore keyfile /path/to/key
dvc remote modify --local httpdata ask_password true
```

## Cache Directory

`dvc cache dir` reads or writes the local cache base directory.

```bash
dvc cache dir
dvc cache dir /path/to/shared-dvc-cache
dvc cache dir --local /fast/local/cache
dvc cache dir --unset
```

Notes:

- Without an explicit configured value, the default is the repo `.dvc/cache` directory.
- Relative cache paths are resolved relative to the current directory and saved relative to the config file location.
- Shared cache layouts may need `dvc gc -p/--projects` so one project does not remove data needed by another.

## Cache Link Types and Protection

DVC cache link types are validated against this set:

```text
reflink, hardlink, symlink, copy
```

Examples:

```bash
dvc config cache.type reflink,copy
dvc config cache.type hardlink,copy
dvc config cache.shared group
dvc checkout --relink
dvc unprotect data/file.csv
```

Behavior to explain:

- Changing `cache.type` affects future checkout/link operations but does not update existing workspace file links by itself.
- After changing `cache.type`, run `dvc checkout --relink` to recreate workspace links or copies from cache.
- `dvc unprotect <targets>` converts protected hardlinked/symlinked tracked files into editable workspace files.
- `cache.shared group` supports group-shared cache permissions where the filesystem and user groups allow it.
- `cache.protected` exists in schema as deprecated; prefer `dvc unprotect` and link-type/relink guidance rather than recommending new `cache.protected` usage.

## Safe Config Editing Checklist

Before editing:

1. Inspect `dvc config --list --show-origin` and `dvc remote list`.
2. Choose the narrowest config level: project for shareable names/URLs, local for secrets and local paths.
3. Check optional backend support with `python scripts/check_remote_support.py --scheme <scheme>` for non-local backends.
4. Validate syntax with help/config commands before any `push`, `pull`, `fetch`, `status -c`, or `gc -c`.
5. Never paste credentials into public project config or generated skill artifacts.
