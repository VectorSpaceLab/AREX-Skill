---
name: harvesting-and-admin
description: "Operate GeoNode harvesting, indexing, asynchronous workers,
  management commands, thesauri, migrations, and backup/restore workflows with
  explicit service gates and recovery safeguards."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Harvesting and administration

Use this sub-skill when a task involves remote catalogue harvesting, search
index maintenance, Celery or async execution, Django management commands,
admin operations, thesauri, migrations, or backup/restore planning. It is an
operational router, not proof that a GeoNode deployment or its external
services are available.

## Safety boundary

- Treat PostgreSQL/PostGIS, GeoServer, Redis/broker, Celery workers/beat,
  remote OGC or ArcGIS endpoints, credentials, writable media/data directories,
  and browser/admin services as explicit prerequisites. None is verified by a
  Python import or by this skill's help wrapper.
- Prefer inspection and `--help`. Never use `--force`, `--skip-read-only`,
  restore, deletion, overwrite, or network harvesting as a default.
- Before any mutating action, identify the target instance, take a tested
  backup, narrow the selection, record the command and expected row/resource
  count, and arrange rollback or recovery. Do not run production changes just
  to validate a command.
- Keep secrets out of shell history and logs. Do not pass passwords on command
  lines when an environment-specific secret mechanism is available.

## Route the request

1. **Harvesting or a stalled asynchronous operation:** read
   [harvesting-and-async.md](references/harvesting-and-async.md), then
   [troubleshooting.md](references/troubleshooting.md). Separate remote URL,
   database, broker, worker queue, and GeoServer gates before retrying.
2. **Command selection, migration, reindex, sync, or thesaurus:** read
   [management-commands.md](references/management-commands.md). Discover
   syntax with the bundled help wrapper; classify help-only, local-mutating,
   destructive, and service-backed operations before execution.
3. **Backup or restore:** read
   [backup-restore-and-safety.md](references/backup-restore-and-safety.md) and
   the recovery section of [troubleshooting.md](references/troubleshooting.md).
   Validate archive/config/space and the recovery file before considering a
   restore. A restore overwrites the target by default.
4. **Unknown failure, stuck state, or partial result:** use the decision tree
   in [troubleshooting.md](references/troubleshooting.md), preserve logs and
   session/job identifiers, and stop at the first unverified service gate.

## Minimal operating sequence

1. Record the GeoNode release/snapshot, settings module, target environment,
   operator permissions, and whether this is a disposable copy.
2. Run `python scripts/manage_help.py --help` to inspect the wrapper, then use
   `--project-root` with `--command-help COMMAND` or `--list-commands`. The
   wrapper is help/list only; it does not execute an arbitrary command.
3. For a management command, run its help first, inspect the source/documented
   preconditions, select the narrowest filter and dry-run option, and capture
   stdout/stderr. The wrapper cannot make a mutating command safe.
4. Verify expected observations: status transitions to `ready`, a session/job
   reaches a terminal state, selected index rows are rebuilt, archive and MD5
   files exist, or a migration/check reports success. Confirm the actual DB,
   catalogue, and file effects separately.
5. If a step fails, do not blindly rerun. Record the command, options, session
   or job id, queue/worker, traceback, and last successful stage; use the
   recovery guidance before retrying.

## Acceptance gates

A result is acceptable only when the command's side effects and prerequisites
are classified. Help output alone proves parser availability, not database,
GeoServer, broker, remote endpoint, permission, or data correctness. For
harvesting, require remote availability plus completed refresh/harvest session
signals. For indexing/sync, require the correct database and, where used,
GeoServer/catalogue services. For backup, verify archive integrity and a
separate recovery plan. For restore, use an isolated target and verify
fixtures, media/assets, GeoServer state, and the recorded restore history.

## Bundled helper

`scripts/manage_help.py` accepts an explicit project root or an installed
`manage.py`/entrypoint, lists commands, or prints one command's help. It
rejects command arguments other than its own safe list/help modes and never
runs a mutating management command. See the command matrix and examples in
[management-commands.md](references/management-commands.md).

## Scope and links

This sub-skill owns harvesting/indexing, async/Celery administration,
management-command safety, thesauri, migrations, backup/restore, and
operational recovery. Route installation and service provisioning to the setup
sub-skill; route resource/API payload mechanics to the resource/API sub-skill;
route GeoServer authentication and publication internals to the GeoServer and
security sub-skill. Those boundaries do not remove the service gates stated
here.
