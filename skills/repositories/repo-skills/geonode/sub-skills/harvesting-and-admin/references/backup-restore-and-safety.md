# Backup, restore, and safety

## Capability and prerequisites

GeoNode's `br` application serializes Django fixtures, media/assets, database
content, and GeoServer catalog/data according to an INI configuration. The
backup archive is not a generic PostgreSQL dump: it also contains ordered
fixtures and optional GeoServer state/data. The `br` app itself is excluded
from fixture dumps because it is instance-specific.

Before a real backup or restore, confirm all of the following in the target
runtime, not from this skill:

- PostgreSQL/PostGIS is reachable and `pg_dump`, `pg_restore`, and `psql` are
  installed with compatible versions and permissions;
- GeoServer is reachable with the configured credentials and its backup/restore
  extension supports the deployed GeoServer version;
- the GeoServer data directory is the correct shared path and is writable by
  the participating processes;
- the GeoNode media/assets roots and temporary/archive locations have enough
  free space and appropriate ownership;
- the INI `[fixtures]` `apps` and `dumps` lists are aligned and intentionally
  ordered;
- the target is in a maintenance window and incoming writes/uploads/tasks are
  quiesced or read-only behavior has been independently confirmed;
- a separate recovery archive/snapshot exists and its restore procedure was
  tested on a disposable target.

External database, GeoServer, Redis/Celery, credentials, shared volume,
filesystem permission, and Docker gates are unverified in this construction.

## Configuration model

Use a copy of the version-matched sample INI and inspect every value before
execution. The relevant sections are:

```ini
[database]
pgdump = pg_dump
pgrestore = pg_restore
psql = psql

[geoserver]
datadir = /path/to/geoserver/data
dumpvectordata = yes
dumprasterdata = yes
# optional: datadir_exclude_file_path, data_dt_filter,
# data_datasetname_filter, data_datasetname_exclude_filter

[fixtures]
apps = contenttypes,auth,...
dumps = contenttypes,auth,...
```

`apps` and `dumps` must have the same intended order. GeoServer options can
include/exclude data by modification time or dataset name; document filters
before using them. In a Docker deployment, use the shared backup/restore
volume and the Docker-specific sample's GeoServer data directory. Do not use
the GeoServer data directory itself as the archive destination because
recursive backups can result.

Treat the INI as sensitive operational configuration: it can name paths and
commands, and the archive can contain users, credentials, permissions, media,
styles, and data. Restrict file permissions and access.

## Backup planning and command behavior

Discover syntax first:

```bash
python manage.py backup --help
```

The command requires `--backup-dir`. It also accepts `--config`, GeoServer
vector/raster selection flags, `--skip-geoserver`, `--ignore-errors`,
`--skip-read-only`, `--skip-logger-setup`, and `--force`. The safe default is
to retain read-only mode and interactive confirmation; do not use `--force` or
`--skip-read-only` merely to automate a first run.

A normal backup stages GeoServer catalog/data (unless skipped), dumps ordered
Django fixtures with signals disabled, copies media/assets, creates a ZIP,
creates a matching `.md5`, saves the effective INI, and removes the temporary
staging directory. Verify each stage. The backup command may make temporary
folders writable and contacts GeoServer; it is not safe to run against an
unreviewed or low-disk target.

After completion, record:

- archive path, size, timestamp, and SHA/MD5 file;
- output INI and exact source settings revision;
- included/excluded GeoServer data and fixture app list;
- database/catalogue/media/assets row/file counts;
- logs, warnings, and any `--ignore-errors` omissions.

Validate the archive independently with a ZIP listing and by comparing the
recorded MD5. A valid ZIP is not proof that every fixture, database table,
GeoServer layer, or media file was captured.

## Restore planning and overwrite warning

Discover syntax only:

```bash
python manage.py restore --help
```

The command requires exactly one of `--backup-file` or `--backup-files-dir`.
A direct backup file must be an existing ZIP. A directory selects the newest
ZIP according to its timestamps and restore history. It also supports:

- `--config` or the INI stored with the archive;
- `--recovery-file` for an archive to use if restoration fails;
- `--with-logs` to reject an archive already recorded as restored by MD5;
- `--skip-geoserver`, `--skip-geoserver-info`, and
  `--skip-geoserver-security` to narrow GeoServer restoration;
- `--soft-reset` to preserve GeoServer tables/resources rather than the default
  drop/reset behavior;
- `--notify`, `--ignore-errors`, `--geoserver-data-dir`, `--force`, and
  `--skip-read-only`.

**Restore overwrites the whole target GeoNode instance and, by default,
GeoServer state/data.** It can replace database fixtures, users, permissions,
media/assets, layers, styles, and service configuration. `--soft-reset` is not
a general safety guarantee; it changes GeoServer preservation behavior while
other target data can still be replaced. `--skip-geoserver` does not make a
restore safe for the GeoNode database.

A safe restore runbook is:

1. Name the target explicitly and stop if it is not disposable or in an
   approved maintenance window.
2. Verify the archive ZIP, matching `.md5`, stored/current INI, creation date,
   expected version, and free space. Extract/list it in a separate temporary
   directory without touching the target.
3. Verify the recovery file is a known-good, independently restorable archive.
   Do not use the same archive as both input and recovery file unless that is an
   intentional, tested policy.
4. Take a fresh target backup/snapshot, record DB/GeoServer/media/assets
   versions and service endpoints, and quiesce Celery/beat/uploads.
5. Run without `--force` first; preserve read-only mode. Choose skip/soft-reset
   options only after documenting the intended resulting state.
6. Monitor logs and disk space. Preserve the restore temp directory/logs if the
   procedure fails; do not delete evidence before diagnosis.
7. Verify DB migrations/fixtures, admin login, permissions, resource counts,
   media/assets, GeoServer workspaces/stores/layers/styles, public/internal
   URLs, catalogue XML, and Celery settings independently.
8. If the restore was from another host, plan `migrate_baseurl` and metadata/
   link regeneration as a separate controlled operation. Verify OAuth/redirect,
   proxy, DNS, and TLS afterward.
9. Record the restored archive's MD5 and history row, deviations, and any
   skipped GeoServer/security sections.

`--force` bypasses the confirmation; `--skip-read-only` removes a protection;
`--ignore-errors` can leave a partial archive/restore; and `--notify` can
expose failure details through mail. None is a repair switch.

## Recovery files and partial failure

The restore implementation creates a unique extraction/staging directory and
can use `--recovery-file` to restore original content if failure handling is
configured. A recovery file is not a transaction across external GeoServer and
filesystem state. If failure occurs:

- preserve command output, logs, archive/MD5/INI, target and recovery paths,
  selected flags, and the last completed stage;
- keep the target read-only/quiesced and prevent new workers from mutating it;
- determine whether the failure is preflight (invalid ZIP/MD5/config/space),
  database/fixture, media/assets, GeoServer catalog/data, or post-restore URL/
  metadata synchronization;
- do not rerun restore with `--force` or delete the target to “clear” the error;
- use the tested recovery archive/snapshot on an isolated target first, then
  restore the target only with an approved plan;
- after recovery, inspect `RestoredBackup` history and MD5 behavior; a history
  entry or a completed command does not prove application correctness.

For a backup that partially completed, treat the archive as untrusted until
its contents and counts are checked. `--ignore-errors` should be reported as a
known omission, not accepted as successful completeness.

## Safe validation hierarchy

1. **Parser-only:** wrapper or `manage.py backup/restore --help`.
2. **Static/config-only:** parse a copied INI, verify fixture list alignment,
   inspect paths, command availability, ZIP/MD5 without contacting services.
3. **Disposable backup:** run on a small isolated dataset with explicit temp
   roots and no production credentials, then inspect all archive classes.
4. **Disposable restore:** restore into a separate full stack, verify each
   subsystem, and document any service-dependent failures.
5. **Production:** only after the prior gates and a tested recovery plan.

The current construction performed no real backup or restore. PostgreSQL,
GeoServer, writable data directories, credentials, and service orchestration
remain unverified prerequisites.
