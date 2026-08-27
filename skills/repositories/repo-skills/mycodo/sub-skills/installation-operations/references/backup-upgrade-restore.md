# Backup, Restore, Import, Export, And Upgrade

Read this before touching Mycodo backups, settings imports, measurement exports, upgrades, or post-upgrade recovery. These operations can alter databases, custom modules, services, and environmental control state.

## Safety gates

Before any mutating action, confirm:

1. Target host and install path are correct.
2. Environmental Outputs/PID/Conditional/Trigger logic are in a safe state for downtime.
3. A current backup exists or the user accepts data-loss risk.
4. The user knows whether they are moving **settings**, **measurements**, or both.
5. Version compatibility is checked: settings imports are safe only when the backup's Mycodo and database versions are not newer than the destination and the major version matches.

## Backup workflow

The web UI path is `[Gear Icon] -> Backup Restore`. Mycodo normally writes backups to `/var/Mycodo-backups`; upgrades also create backups. Prefer the web UI when it is available because it captures expected metadata and status.

Installed CLI entry points may include:

```bash
sudo mycodo-commands backup-create
sudo mycodo-commands backup-restore /var/Mycodo-backups/<backup-directory>
```

Only use CLI forms after confirming the target backup directory, because restore can replace settings, custom modules, and service state. Backup creation writes to `/var/log/mycodo/mycodobackup.log`; restore writes to `/var/log/mycodo/mycodorestore.log`.

Important backup content caveat: the backup creation path copies the Mycodo install while excluding the virtualenv, camera directory, and active upgrade marker. Do not assume camera captures or Python environment files are preserved unless the backup contents and deployment policy are inspected.

## Restore workflow

Use the web UI restore button when available. If the UI is inaccessible, the documented CLI shape is:

```bash
sudo mycodo-commands backup-restore /var/Mycodo-backups/<backup-directory>
```

Before running it, inspect the backup directory name/version, read recent `mycodorestore.log` if a restore was attempted, and ask the user to confirm that current settings may be overwritten.

## Export/import workflow

The Export Import page can export measurements as CSV for a selected date/time range and can export/import measurement database archives. It can also export/import settings ZIP files containing the settings SQLite DB and custom controllers.

Important compatibility rules:

- Measurement imports add to current measurement data; they do not by themselves recreate the settings/controllers that make measurements visible in dashboards.
- Measurements are associated with IDs for Inputs, Outputs, and other controllers. If the matching settings/controllers are not imported too, historical measurements may exist but not appear on graphs.
- Settings import overwrites current settings and custom controller data. Treat it as destructive and create a backup first.
- Settings imports require the same major version and destination versions equal to or newer than the source backup.

## Upgrade workflow

Recommended path: use `[Gear Icon] -> Upgrade` from the web UI. The documented CLI path is:

```bash
sudo mycodo-commands upgrade-mycodo
```

Upgrade logs are written to `/var/log/mycodo/mycodoupgrade.log` and are also visible from the Mycodo Logs page when the UI works. The upgrade process stages a new release, moves the previous install into `/var/Mycodo-backups`, preserves runtime data such as SQLite databases, SSL certificates, custom Inputs, Outputs, Functions, Actions, Widgets, user scripts/code/assets, notes, usage reports, and cameras when present, then runs post-upgrade initialization, package/dependency updates, Alembic migration, web server update, logrotate update, permissions, daemon restart, and web check.

If the web UI is inaccessible after an upgrade, first inspect the upgrade log. Prefer the installed command wrapper for post-upgrade recovery:

```bash
sudo mycodo-commands upgrade-post
```

If the wrapper is unavailable but the installed tree is intact, the installed script path `/opt/Mycodo/mycodo/scripts/upgrade_post.sh` is the underlying recovery target. Run either form only on the live installed host after confirming the user accepts service/database mutation.

## Incorrect database version recovery

Symptoms:

- System Information page shows database version in red.
- Logs mention migration/version mismatches.
- UI loads partially but settings/controllers fail.

First actions:

1. Inspect `/var/log/mycodo/mycodoupgrade.log` for migration errors.
2. Check current Mycodo version and Alembic version from System Information.
3. Determine whether the issue started after an old upgrade, restore, or settings import.

As a last-resort fresh-start path, docs describe renaming the settings DB and restarting the web UI:

```bash
mv /opt/Mycodo/databases/mycodo.db /opt/Mycodo/databases/mycodo.db.backup
sudo service mycodoflask restart
```

This effectively starts with no existing configuration. Do not use it until the user accepts loss of active settings and has a backup or does not need the old config.

## Troubleshooting signals

| Symptom | Likely source | Next step |
| --- | --- | --- |
| UI inaccessible after upgrade | failed post-upgrade step, frontend/nginx error, DB migration issue | inspect `mycodoupgrade.log`, `mycodoflask` status, nginx error log |
| Restore completed but graphs missing data | settings/controller IDs missing or measurement window mismatch | verify settings import plus measurement import; inspect dashboard/widget controller IDs |
| Import fails on version | major version mismatch or source newer than destination | upgrade destination first or use a compatible backup |
| Backup directory not visible | wrong path/permissions or nonstandard install | list `/var/Mycodo-backups`, check backup log |
| InfluxDB data absent | measurement DB not running/configured, skipped local DB, remote creds wrong | probe `/ping`, verify Mycodo measurement DB settings |
