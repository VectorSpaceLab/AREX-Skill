# Data and Storage Troubleshooting

Use this guide to triage data/storage issues conservatively. Prefer read-only inspection, bounded local tests, and explicit skip reasons before running server-backed, cloud-backed, or destructive operations.

## Datatype Problems

| Symptom | Likely Cause | Conservative Response |
| --- | --- | --- |
| Upload auto-detect is slow or memory-heavy | Sniffer reads the full file, iterates to EOF, or parses complete JSON/XML/archive content | Use bounded prefix/header logic; run `scripts/check_datatype_sniffer.py`; add large negative sample tests. |
| New format never appears in upload format list | Missing datatype registration or `display_in_upload` not set | Check class `file_ext`, registration extension, and upload display intent. |
| New class is ignored at startup | Wrong module/class path or missing import path | Verify type path and importability in the target environment; keep registration extension aligned. |
| Wrong datatype wins auto-detect | Sniffer order is too broad or too early | Move rigid sniffers earlier and broad fallback sniffers later; add negative tests for neighboring formats. |
| Metadata missing in tool filters | `MetadataElement` absent, wrong default/no-value, or `set_meta` not populating it | Add explicit metadata contract and focused `set_meta` tests. |
| Composite dataset component paths break after datatype change | Metadata-backed component filenames are lost | Disallow datatype changes for fragile composites or preserve required metadata. |

## Data Manager and Table Problems

| Symptom | Likely Cause | Conservative Response |
| --- | --- | --- |
| Data manager does not load | Malformed XML, duplicate ID, wrong `tool_file`, or server restart missing | XML-parse the config, confirm unique IDs, and restart/reload only in a controlled instance. |
| Data manager runs but table row is absent | JSON missing top-level `data_tables`, wrong table name, or row shape mismatch | Validate JSON output and ensure table columns match row keys. |
| Table select is empty | `.loc` path missing, wrong table config file, wrong table name, or filter columns mismatch | Check table config, `.loc` row count/columns, and tool filter column indexes. |
| Paths point at the wrong storage area | `target`/`value_translation` templates use wrong base or relative path | Confirm data-manager data path vs tool-data path and the order of move then translation. |
| Duplicate or stale reference entries | Non-unique `value` IDs or destructive row edits | Prefer stable unique IDs and append versioned rows when compatibility matters. |

## Object Store Problems

| Symptom | Likely Cause | Conservative Response |
| --- | --- | --- |
| Object-store config fails to instantiate | Missing optional dependency, wrong backend type, malformed XML/YAML, or missing cache path | Validate local model/config shape before remote tests; install optional backend only with approval. |
| User object-store selection unavailable | Primary object store is not distributed | Route to admin configuration planning; templates alone cannot enable selection. |
| Remote datasets intermittently fail | Cache path/size, staging path, remote existence checks, or backend network instability | Reproduce with local/distributed tests first; require credentials and disposable resources for remote checks. |
| Dataset privacy changes unexpectedly | Misconfigured `private` flag, badges, or user object-store serialization | Review privacy/security flags and serialization tests before migration. |
| Cloud integration tests fail locally | Required `GALAXY_TEST_*` credentials or services are absent | Skip with explicit credential/backend requirement; do not invent dummy secrets. |

## File Source Problems

| Symptom | Likely Cause | Conservative Response |
| --- | --- | --- |
| POSIX source can read through symlink unexpectedly | Symlink security disabled or allowlist too broad | Keep symlink enforcement on unless the target path is intentionally allowlisted. |
| Write fails under a file source | `writable` false, parent creation disabled, role/group restriction, or backend read-only | Confirm desired write behavior and access policy before changing config. |
| OAuth file source fails | Missing client credentials, refresh token, callback URL, or scope mismatch | Keep secrets out of logs; route admin client setup to configuration guidance if needed. |
| User can browse but not import | Source is browsable but not writable/importable, or permissions differ by user context | Inspect capability flags and role/group requirements. |
| Credentialed tests are skipped | Environment variables or external test service are absent | Record skip reason and use local/template tests for code changes. |

## Cleanup and Migration Caveats

Cleanup and object-store migration operations can permanently change database state or remove files. Before suggesting execution, require:

1. A confirmed target Galaxy instance and scope.
2. A current database and object-store backup.
3. Read-only or info-only output reviewed by the user.
4. Explicit confirmation for `remove_from_disk`, purge, delete, force-retry, migration, or post-copy source removal modes.
5. A rollback plan and maintenance window for production.

If any of these are missing, stop at analysis and provide a safe checklist instead of a command.

## Hard Usability Cases

- Review a new datatype implementation whose sniffer uses a mix of `read()`, archive inspection, and metadata extraction; identify full-file read risks, missing registration, missing metadata tests, and safer bounded alternatives.
- Triage a failing object-store test where local distributed-disk tests pass but S3/Azure integration is skipped; classify which checks are safe locally, which require credentials, and what skip reason should be documented.
