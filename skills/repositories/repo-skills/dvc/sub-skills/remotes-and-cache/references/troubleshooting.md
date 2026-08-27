# Remote and Cache Troubleshooting

Use this reference to diagnose remote/cache errors without running cloud transfers or touching credentials unnecessarily.

## Missing Optional Backend Dependencies

Symptoms:

- `RemoteMissingDepsError`
- `URL 's3://...' is supported but requires these missing dependencies: ...`
- Import errors for modules such as `dvc_s3`, `dvc_gs`, `dvc_azure`, `dvc_ssh`, `dvc_webdav`, or `dvc_webhdfs`.

Safe checks:

```bash
python scripts/check_remote_support.py --scheme s3
python scripts/check_remote_support.py --all
```

Fix mapping:

| Scheme | Narrow pip install advice |
| --- | --- |
| `s3://` | `pip install 'dvc[s3]'` |
| `gs://` | `pip install 'dvc[gs]'` |
| `azure://` | `pip install 'dvc[azure]'` |
| `oss://` | `pip install 'dvc[oss]'` |
| `ssh://` | `pip install 'dvc[ssh]'`; use `pip install 'dvc[ssh_gssapi]'` only for GSSAPI needs. |
| `hdfs://` | `pip install 'dvc[hdfs]'` |
| `webdav://`, `webdavs://` | `pip install 'dvc[webdav]'` |
| `webhdfs://` | `pip install 'dvc[webhdfs]'`; use `pip install 'dvc[webhdfs_kerberos]'` only for Kerberos needs. |

Avoid broad `dvc[all]` unless the user explicitly needs many backends. The optional extras are not installed by default.

## Unsupported URL Scheme

Symptoms:

- `Unsupported URL type <scheme>://`
- `import-url` or remote validation fails before authentication.

Checks:

```bash
dvc import-url --help
dvc remote add --help
python scripts/check_remote_support.py --scheme <scheme>
```

Recovery:

- Confirm the URL uses one of DVC's supported schemes: local path, HTTP(S), `s3`, `gs`, `azure`, `oss`, `ssh`, `hdfs`, `webdav`, `webdavs`, `webhdfs`, or `remote`.
- For paths on Windows, be careful not to misread drive letters as unsupported URL schemes.
- For a named DVC remote reference, use `remote://remote_name/path`, not an arbitrary provider alias.

## No Default Remote

Symptoms:

- `No remote provided and no default remote set.`
- `no remote specified ... Setup default remote`
- `dvc push`, `dvc pull`, `dvc fetch`, or `dvc status -c` has no remote target.

Checks:

```bash
dvc remote list
dvc remote default
dvc config core.remote
dvc config --list --show-origin
```

Recovery:

```bash
dvc remote add -d localremote /path/to/local-dvc-remote
# or, if the remote already exists:
dvc remote default localremote
# or override per command:
dvc push -r localremote
```

If `remote default <name>` fails, verify the remote exists at the same or a lower-precedence config level.

## Remote Not Found or Renamed

Symptoms:

- `remote '<name>' doesn't exist`
- `default remote must be present in remote list`
- A command references an old remote name after rename/remove.

Checks:

```bash
dvc remote list
dvc config --list --show-origin | grep -E '(^|\.)remote'
```

Recovery:

- Use `dvc remote rename old new` rather than manually editing multiple config files when preserving a remote.
- Use `dvc remote default --unset` if the default points at a removed remote.
- Re-add the remote with `dvc remote add <name> <url>` if the config was removed accidentally.

## Authentication and Credentials

Symptoms:

- Auth errors from cloud SDKs, HTTP 401/403, SSH permission denied, invalid token, credential file not found.
- Prompting for passwords unexpectedly in noninteractive runs.

Safe checks:

```bash
dvc remote list
dvc config --list --show-origin
python scripts/check_remote_support.py --scheme <scheme>
```

Recovery principles:

- Keep secrets and local credential paths in `--local` config.
- For HTTP/WebDAV, consider `ask_password true`, `user`, `ssl_verify`, bearer token command, or provider-specific auth settings.
- For SSH, check `user`, `port`, `keyfile`, `ask_passphrase`, `allow_agent`, and `gss_auth` only if the user expects those auth modes.
- For S3/GS/Azure, prefer provider profiles or credential files over pasting raw keys into shared config.
- Do not run login flows or credentialed network checks unless the user explicitly approves them.

## Missing Cache or Not in Cache

Symptoms:

- Status output says an output is `not in cache`.
- `pull` or `checkout` cannot materialize workspace files.
- An imported URL stage exists but data is absent locally.

Checks:

```bash
dvc status
dvc status -c -r <remote>
dvc remote list
dvc config --list --show-origin
```

Important correction: DVC has `gc --dry`, but `fetch` and `pull` do not expose a dry-run flag in this checkout. For no-mutation diagnosis, use `dvc status`, `dvc status -c`, and config inspection. If the user approves a real transfer, use `dvc fetch` to populate cache without checkout, then `dvc checkout` to materialize files.

Recovery:

```bash
dvc fetch -r <remote> <target>
dvc checkout <target>
dvc pull -r <remote> <target> --allow-missing
```

If data was intentionally imported with `dvc import-url --no-download`, explain that the stage metadata may exist while the data still needs a later `dvc pull` or `dvc fetch` from the configured remote/cache.

## Cache Link, Relink, and Unprotect Issues

Symptoms:

- Workspace files are read-only or edits affect cache-linked data unexpectedly.
- Changing `cache.type` does not change existing files.
- Unsupported cache type error.

Checks:

```bash
dvc config cache.type
dvc cache dir
dvc status
```

Recovery:

```bash
dvc config cache.type reflink,copy
dvc checkout --relink
dvc unprotect <tracked-file-or-dir>
```

Only `reflink`, `hardlink`, `symlink`, and `copy` are valid cache link types. `dvc unprotect` is for tracked targets when hardlinks or symlinks are enabled.

## Garbage Collection Safety

Symptoms:

- User wants to reclaim space but is unsure whether data is still needed.
- Shared cache is used by multiple projects.
- User asks to clean a remote.

Safe checks:

```bash
dvc gc --dry
dvc gc --dry --all-branches --all-tags
dvc gc --dry -p /path/to/other-project
dvc gc --dry -c -r <remote>
```

Recovery principles:

- Never skip the explanation before `dvc gc -c`; it affects remote storage too.
- Use `-p/--projects` for shared caches.
- Use `--not-in-remote` when local objects not present in the remote should be preserved.
- Use `-f/--force` only when the user accepts the deletion scope.

## Network Skip Boundaries

Classify these as skip-network/credentials unless the user explicitly authorizes them:

- Real S3/GS/Azure/OSS/SSH/HDFS/WebDAV/WebHDFS push, pull, fetch, status, list, or gc operations.
- Tests or examples that require cloud fixtures, remote servers, credentials, SSH keys, Docker services, or provider emulators.
- Any command that could upload, download, delete, or list private remote data.

Safe alternatives:

- `dvc <command> --help`
- `dvc config --list --show-origin`
- `dvc remote list`
- `python scripts/check_remote_support.py --all`
- Local filesystem remote examples in a disposable directory when mutation is acceptable.
