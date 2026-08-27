# Troubleshooting and operational recovery

Use this reference as a stop-and-classify procedure. Preserve the target
state, command line, settings revision, session/job id, queue, timestamps,
logs, and traceback before changing anything.

## First classification

| Observation | First gate | Do not infer |
|---|---|---|
| Import/help works but command action fails | Django settings, database, permissions, command-specific prerequisites | Package import does not prove a live service. |
| Harvester `remote_available=False` | DNS/TLS/auth/proxy/remote API or OGC capabilities from the worker network | A saved `remote_url` is reachable. |
| Harvester `ready` but no session | Scheduler, API/admin action, DB row/session creation, Celery dispatch | A scheduler process or beat is running. |
| Session `pending` / job `QUEUED` | Broker URL, broker health, queue routing, registered worker | Celery package installation means a worker consumes that queue. |
| Session `on-going` with no progress | Worker logs, database connections/locks, remote latency, task expiry, memory/time limit, monitor | It is safe to launch a duplicate session. |
| Terminal session with stale busy status | Finalizer/error handler and exact session id | Reset completes missing work or rolls back changes. |
| Index command fails | PostgreSQL/PostGIS and metadata settings/index schema | SQLite or a mocked manager validates PostgreSQL tsvectors. |
| Sync/import fails | GeoServer URL/credentials/catalogue/GeoFence and local DB | HTTP 200 from the web app means GeoServer is healthy. |
| Restore fails | ZIP/MD5/config/space first, then DB/files/GeoServer stage | `--force`, `--ignore-errors`, or rerun is recovery. |

## Harvesting decision tree

### A. No resources discovered

1. Check harvester type import and JSON schema against the intended worker.
2. Check `remote_url` normalization and service-specific endpoint:
   - GeoNode: remote `/api/v2/resources/` and permitted resource types;
   - WMS: `GetCapabilities`, version, leaf layers, CRS/bounds, XML response;
   - ArcGIS: catalog or supported `MapServer`/`ImageServer`, JSON response.
3. Run availability check and compare `remote_available`, timestamp, response
   status, and worker log. Inspect auth/proxy/TLS from the Celery worker's
   network namespace.
4. Check filters: title/name, dates, keywords/categories, service names, and
   dataset/document toggles can legitimately reduce the result to zero.
5. Inspect refresh session status/details/counts. Do not perform harvesting if
   the refresh did not complete or the result set was not reviewed.

### B. Refresh completes but local rows are stale or missing

1. Confirm the refresh session reached a terminal state and its
   `total_records_to_process`/`records_done` values are plausible.
2. Check whether pagination/batch tasks were routed to a worker and whether
   the finalizer ran. Inspect the harvester's last refresh time/message.
3. Compare the remote identifiers and titles with `HarvestableResource` rows;
   title changes are updated, but stale rows may be removed after a successful
   refresh. `delete_orphan_resources_automatically` controls whether a linked
   local resource is also deleted.
4. If worker configuration changed, expect the API/admin flow to delete old
   harvestable rows and schedule a new refresh. Review before enabling selection.
5. Re-run one scoped refresh only after capturing the old session evidence.

### C. Harvest session has failures

1. Inspect every resource's `last_harvesting_message`, success flag, and
   timestamp plus the session `details` and `records_done`.
2. Separate remote retrieval failure (`get_resource`), local descriptor/model
   update, GeoServer/publication, storage, and indexing/catalogue follow-up.
3. Keep successful local links. Retry only failed, approved resources after the
   remote and local cause is fixed; do not launch the entire set blindly.
4. If the monitor force-finalized a session, preserve the execution request
   id and monitor/error traceback. Treat `finished-some-failed` as a partial
   result requiring review, not as a successful harvest.
5. If aborting, wait for the chord/finalizer and verify terminal status. Celery
   revoke is not the model's abort strategy; the session state coordinates
   pending/in-flight work.

## Celery and management jobs

### Queued forever

Check, in order:

1. `ASYNC_SIGNALS` and broker/result URLs in the web and worker environments;
2. broker reachability and credentials from the worker;
3. worker registration (`celery inspect active`, queues, or deployment-native
   equivalent) without exposing secrets;
4. that a harvesting worker consumes `harvesting`, a general worker consumes
   `geonode`, and the HTTP job worker consumes `management_commands_http`;
5. beat schedule/state and duplicate beat processes for periodic work;
6. task expiration, result backend, and event/started tracking settings.

In development/tests `CELERY_TASK_ALWAYS_EAGER=True` can make a task appear to
work without a broker. That is a useful unit signal only. Do not “fix” a
production queue by enabling eager mode: it changes execution semantics and
can run work in the web process.

### Job started but no output

Find the job's persisted args/kwargs, start time, Celery result id, output, and
traceback. Identify whether the command is waiting on a remote service,
database lock, file permission, prompt, or large dataset. HTTP jobs cannot use
`--help`; inspect help locally. Stop terminates a task but does not undo partial
DB/filesystem/GeoServer changes. For a mutating job, switch to the command's
recovery plan rather than resubmitting.

### HTTP command not listed or rejected

- Inspect the effective `MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP`, including
  environment additions, in the target settings.
- Confirm URL prefix and trailing slash, authentication, and superuser status.
- A command omitted from the allowlist is intentionally unavailable.
- `--help` is rejected in job args; use `manage_help.py` or local
  `manage.py COMMAND --help`.
- A listed command still needs its own DB/GeoServer/filesystem prerequisites.
  Remove high-risk commands from the allowlist unless there is a reviewed
  admin-only operational reason.

## Indexing, migration, thesaurus, and sync failures

### Reindex

- `relation does not exist`, connection, or `to_tsvector` errors: stop and
  verify PostgreSQL/PostGIS, migrations, extension/schema, and metadata index
  settings. Do not substitute SQLite.
- Wrong language results: inspect `MULTILANG_FIELDS`, configured languages,
  fallback title content, and both localized and `lang=NULL` rows.
- Too broad or expensive: use `--dry-run` and repeated `--uuid`; record failed
  UUIDs and rerun only after fixing the first cause.

### Migrations

- Run `showmigrations` and capture the database alias/settings before `migrate`.
- If a migration fails, preserve the DB error and migration name; do not mark
  it applied or continue with a second application.
- Confirm code/database compatibility and a backup. `migrate` can alter schema
  and data; it is not a harmless startup check.
- Container startup may run migrations, fixtures, static collection, and
  thesaurus autoload in sequence. Identify which stage failed before restarting
  repeatedly.

### Thesaurus

- `ConceptScheme not found`: inspect RDF syntax/format and ensure the input
  contains exactly one SKOS ConceptScheme.
- Existing identifier: use `append`/`update` deliberately; do not switch to
  `create` repeatedly.
- Unexpected labels: check language tags, `--langs`, default language,
  identifier inference from filename, and action semantics.
- Dump errors: verify identifier, output directory, supported format, and
  prefix/suffix filter syntax. Use `sorted-xml` for stable diffs.
- Autoload problems: preserve the app/file name and continue reviewing the
  remaining files; do not assume a partial count is complete.

### URL or GeoServer sync

After `migrate_baseurl`, check stored links, metadata XML, `csw_anytext`,
current Site, OAuth redirect URIs, GeoServer public/proxy URLs, reverse proxy,
DNS/TLS, and async callback URLs. Then use narrowly filtered metadata/XML/sync
commands. If GeoServer is unavailable, do not run commands that recalculate
attributes, thumbnails, permissions, BBOX, or metadata from it; repair service
connectivity first.

## Backup/restore incident response

### Backup failed or looks incomplete

1. Preserve the archive/staging path and command logs.
2. Check disk space, write permissions, DB tool versions, GeoServer reachability,
   fixture app/dump alignment, and any `--ignore-errors` warnings.
3. Verify ZIP structure and MD5. Compare fixture/media/assets/data counts with
   the source. Do not call the archive usable because a ZIP was created.
4. Take a fresh complete backup after the cause is fixed; do not append to an
   unknown partial archive.

### Restore preflight failed

If ZIP, MD5, config, extension, exclusive option, or free-space validation
fails, do not add `--force`. Correct the artifact or config, verify again, and
keep the target unchanged. If `--backup-files-dir` found no eligible archive,
inspect timestamps and restore history rather than selecting an arbitrary file.

### Restore failed after mutation began

1. Stop web/worker/beat writes and preserve logs, target state, extraction
   directory, selected flags, and exact archive/recovery paths.
2. Identify whether the failure was DB fixture loading, media/assets copy,
   GeoServer catalog/data, permissions, or final cleanup.
3. Do not rerun on the same live target. Test `--recovery-file` or a full target
   snapshot on an isolated copy first; external GeoServer/filesystem changes
   may not be transactional.
4. Restore the approved recovery plan, then verify admin login, users,
   resources, files, GeoServer, links, metadata, and queues separately.
5. Inspect `RestoredBackup` history/MD5 and record whether the failed archive
   was partially applied. A stop/termination is not rollback.

## Two difficult synthetic cases

### Stalled harvest with a healthy web page

Inputs: the web home page returns 200; a harvester is `ready`, its refresh
session is `pending`, remote availability was last checked true, and the
harvesting worker is running but only on `geonode`, not `harvesting`. Expected
handling: identify queue routing as the blocker, preserve the pending session,
verify broker and the dedicated queue, route one small refresh, wait for a
terminal session, and only then harvest. Do not reset, duplicate, enable eager
mode, or claim the remote service is the cause.

### Safe base URL migration and backup plan

Inputs: a site is moving from an HTTP host to HTTPS, stored links contain the
old host, GeoServer has a separate public URL, Celery callbacks use the old
host, and no production DB/GeoServer/recovery archive is available. Expected
handling: inventory URL fields and settings, produce a backup/config/recovery
checklist, require a disposable rehearsal, use `migrate_baseurl` without
`--force` and a narrow verification plan, then regenerate metadata/links and
validate proxy/OAuth/Celery callbacks. It must stop before executing a
mutation or claiming service verification.
