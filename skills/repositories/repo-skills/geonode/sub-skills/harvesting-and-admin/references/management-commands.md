# Management commands and admin operations

## Use the safe help wrapper

From an installed GeoNode environment or an explicit project checkout, list
available commands or inspect one parser without running it:

```bash
python scripts/manage_help.py --list-commands --project-root /path/to/project
python scripts/manage_help.py --command-help migrate_baseurl --project-root /path/to/project
python scripts/manage_help.py --command-help backup --project-root /path/to/project
python scripts/manage_help.py --command-help restore --project-root /path/to/project
```

The wrapper accepts `--manage-py PATH` or `--entrypoint COMMAND` instead of a
project root. `--entrypoint` must be an installed executable or a command name
that is safe to invoke for list/help inspection. It forwards only the wrapper's
fixed list/help mode, sets no secrets, and never invokes a command's `handle()`.
Use the project's settings/environment in the shell when Django must load
custom commands. Parser output proves only that command discovery/import and
argument parsing work.

## Command effect matrix

The table is a planning classification, not an execution allowlist. Even a
non-destructive command can be unsafe on production data or can call external
services.

| Command/group | Effect class | Safe first observation / essential precautions |
|---|---|---|
| `check`, `showmigrations`, command `--help`, `thesaurus list`, wrapper list/help | Help/inspection | Usually safe; still load the intended settings and inspect output. `showmigrations` may require DB access. |
| `migrate` | Local schema mutation | Required for a new code version, but apply to a backup/disposable copy first, review migration plan, and verify DB connectivity/backups. Do not claim success without the target DB. |
| `migrate_baseurl` | Broad local URL mutation; may touch OAuth/site data | Requires both source and target addresses and confirmation unless `--force`. It updates maps, map layers, datasets, styles, links, resource metadata/blob fields, current site, and possibly GeoServer OAuth redirect URIs. Inventory matches, backup, run a narrow clone, then validate URLs. Never default `--force`. |
| `reindex` | Local search-index mutation | Supports repeated `--uuid` and `--dry-run`; uses PostgreSQL `tsvector`/`ResourceIndex` and metadata settings. Use `--dry-run`, then a small UUID set before all resources. Verify localized/non-localized indexes. |
| `regenerate_xml` | Local catalogue metadata mutation | Supports repeated layer/id selectors and `--dry-run`; custom uploaded XML is skipped. Use selectors and dry-run first. CSW/catalogue correctness remains service-backed. |
| `thesaurus list` | Read-only DB inspection | Safe way to discover identifiers, cardinality/facet state, and URI. Requires DB. |
| `thesaurus load` | Local vocabulary mutation or parse-only | `--action parse` reads RDF without writes; `create` fails if an identifier exists; `update` creates/updates; `append` adds missing entries. Validate RDF format, identifier, languages, and target before `update`/`append`. |
| `thesaurus dump` | File output/read-only DB | Requires an identifier. Prefer deterministic `sorted-xml`, explicit output path, and a new file. Include/exclude filters allow only one prefix/suffix `*`; diff output before distribution. |
| `thesaurus autoload` | Local vocabulary mutation | Scans installed apps' `thesauri/*.rdf` and runs update semantics. It is idempotent in intent but still changes DB; run after migrations and record loaded files. |
| `set_all_datasets_metadata` | Broad local and often GeoServer/catalogue mutation | Defaults refresh attributes/links; options may remove duplicates, orphaned thumbnails, or UUIDs. Filter by dataset/owner; no global run without backup and service checks. |
| `sync_geonode_datasets`, `sync_geonode_maps` | Local plus GeoServer synchronization | Narrow by filter/owner. Dataset options update permissions, thumbnails, attributes, BBOX, metadata, or duplicate links. Map options update thumbnails/BBOX/duplicates. GeoServer and possibly GeoFence are required. |
| `updatelayers` | Imports/updates/removes local datasets from GeoServer | Service-backed. Use workspace/store/filter and avoid `--remove-deleted` until an inventory and backup exist. `--skip-geonode-registered` narrows to unregistered layers; `--ignore-errors` changes failure handling, not safety. |
| `importlayers` | Upload/import side effects | Requires a live GeoNode/GeoServer and credentials. Paths may be walked recursively; default credentials in source examples must never be reused. `--skip-existing-layers` is documented as unsupported; do not combine with overwrite. |
| `set_all_datasets_public`, `set_layers_permissions`, permission sync | Access-control mutation | Treat as high impact. Review exact dataset/user/group scope and GeoServer/GovFence synchronization before running. Never expose casually over HTTP. |
| `delete_resources`, orphan cleanup, remove-deleted options | Destructive | No dry-run is implemented for the broad delete command. It accepts filters/config and deletes rows/files; do not run through HTTP or as a validation step. |
| `backup` | Filesystem/DB/GeoServer read plus archive creation | Requires `--backup-dir`, config, DB tools, writable target, and often GeoServer. Default read-only mode is protective; preserve it. Validate archive/MD5/INI outputs. |
| `restore` | Destructive overwrite of target DB/files/GeoServer | Never run on a live target by default. It requires exactly one backup file or directory, validates ZIP/MD5, and supports recovery file, logs, soft reset, skip flags, and read-only mode. See backup reference. |
| HTTP management jobs | Admin-triggered command execution | Only commands explicitly in `MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP`; endpoints require admin/superuser. `ASYNC_SIGNALS=True` and Celery are required for queued execution. The API rejects `--help`; use local help wrapper instead. |

`entrypoint.sh`, `celery-cmd`, and `tasks.py` describe deployment lifecycle and
process topology only. Do not copy them into a helper or run them as a generic
repair command: they can apply migrations, load fixtures/thesauri, collect
static files, alter files/permissions, start long-lived workers, and use
container-specific paths.

## Migration and URL-change planning

For a base URL move, first enumerate the exact canonical old and new strings,
including scheme, host, port, and trailing slash policy. The command performs
substring replacement, not a semantic URL migration. Review false matches and
external links. In a clone or transaction-capable maintenance window:

1. snapshot DB, media/assets, and GeoServer config;
2. update deployment settings (`SITEURL`, GeoServer public/proxy URLs,
   `ALLOWED_HOSTS`, OAuth redirect configuration) consistently;
3. run help and, if available, a filtered/read-only inventory of affected rows;
4. run `migrate_baseurl` without `--force` first so the explicit confirmation is
   visible; capture counts by model;
5. run focused metadata/XML/link regeneration and any required GeoServer/OAuth
   synchronization;
6. test login redirects, resource links, thumbnails, OGC links, catalogue
   metadata, and async callbacks from the public URL;
7. only then repeat the controlled plan in production.

A settings change alone does not rewrite stored `thumbnail_url`, `ows_url`,
style/link URLs, metadata XML, `csw_anytext`, blobs, current Site, or the
GeoServer OAuth application. A successful command does not prove DNS, TLS,
proxy, GeoServer, or catalogue correctness.

## Reindexing and metadata sync

`reindex` builds `ResourceIndex` rows from the metadata manager. Without
multilingual indexed fields it writes one `lang=NULL` tsvector per index; with
multilingual fields it writes one per configured language and fills missing
titles from available/default title content. It removes the opposite index form.
The implementation uses PostgreSQL `to_tsvector`, so SQLite/Spatialite or a
mocked package import is not an equivalent verification.

For a controlled run:

```bash
python manage.py reindex --dry-run --uuid <known-uuid>
python manage.py reindex --uuid <known-uuid>
```

Inspect the command log and `ResourceIndex` rows, then use a representative
multilingual search/filter. `regenerate_xml --dry-run` similarly previews
catalogue metadata scope; use `--layer` or `--id` and verify custom XML is not
silently replaced.

## Thesauri

A thesaurus is a SKOS concept scheme with localized labels and keywords. Its
`card_max` controls whether it is disabled (`0`), single-choice (`1`), or
multi-choice (`-1`), while `card_min` controls optional/required selection;
`facet=True` publishes it as a filter facet. Configure these properties in the
admin only after validating the RDF and intended metadata behavior.

Safe import/export plan:

```bash
python manage.py thesaurus list
python manage.py thesaurus load --file vocabulary.rdf --action parse
python manage.py thesaurus dump --identifier vocabulary --format sorted-xml --out /safe/new/vocabulary.rdf
```

Use `create` for a new identifier, `update` for create-or-update semantics,
`append` to leave existing entries unchanged, and `parse` for no-write
validation. `autoload` discovers RDF files shipped by installed apps and is
normally called during container initialization; inspect logs and the exact
source file set after it runs.

## HTTP-exposed management commands

GeoNode's setting starts with an explicit allowlist including the ping command,
GeoServer dataset/map sync/import commands, dataset metadata, and layer
permissions, and extends it from `MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP`.
The effective list is the security boundary; inspect it in the target settings,
do not assume documentation defaults match project overrides.

Endpoints are under `/api/v2/management/`:

- `GET /commands/`: list exposed commands;
- `GET /commands/<name>/`: return parser help for one exposed command;
- `POST /commands/<name>/jobs/`: create a job with JSON `args`, `kwargs`, and
  optional `autostart`;
- `PATCH /jobs/<id>/start/` and `/stop/`: queue or terminate a job;
- `GET /jobs/<id>/status/`: inspect stored output and Celery task metadata;
- `GET /jobs/`: list/filter audit history.

All endpoints require `IsAdminUser`; use a superuser account according to the
project's auth policy. The create serializer validates that `args` is a list,
`kwargs` a dict, the command is allowlisted, and rejects `--help`. It does not
make an allowlisted command non-mutating: do not expose backup, restore,
delete, migration, public-permission, or unreviewed custom commands. Avoid
putting secrets in JSON args/kwargs because job rows and output are persisted.

Statuses are `CREATED`, `QUEUED`, `STARTED`, and `FINISHED`. A `QUEUED` job with
no worker progress usually means broker/queue/worker configuration or
`ASYNC_SIGNALS` is wrong; a `STARTED` job with no output may be a long-running
command or blocked external service. Stop is task termination, not rollback.
Preserve the job id and output/traceback for recovery.
