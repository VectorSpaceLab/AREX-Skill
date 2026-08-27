---
name: installation-operations
description: "Install, operate, diagnose, back up, restore, upgrade, and
  understand Mycodo deployment layout safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Mycodo Installation Operations

Use this sub-skill when a task is about installing Mycodo, operating an
installed host, diagnosing service/database/log layout, backing up, restoring,
upgrading, or evaluating the experimental Docker deployment. This skill is
self-contained; do not reopen upstream repository docs, examples, installer
scripts, or tests at runtime.

## What This Sub-skill Owns

- Bare-metal Raspberry Pi OS/Debian installation planning and first-login checks.
- Operational layout for `/opt/Mycodo`, `systemd`, nginx, logrotate, InfluxDB,
  SQLite settings database, backups, and Mycodo logs.
- Safe triage of daemon, web UI, InfluxDB, database-version, upgrade, restore,
  import/export, and Docker deployment failures.
- Backup, restore, export/import, upgrade, and post-upgrade recovery workflows,
  with destructive or host-mutating steps explicitly gated.
- The experimental Docker deployment surface, including ports, time zone, named
  volumes, Grafana/Telegraf option, and conflict with local services.

## Route Out Of This Sub-skill

- Custom Input, Output, Function, Action, Widget, or other custom module authoring
  belongs to `custom-modules`.
- REST API, Pyro, `DaemonControl`, and `mycodo-client` automation belongs to
  `api-and-automation`.
- Source checkout maintenance, package development, local tests, and code changes
  belong to `development-and-testing`.
- PID, Conditional, Trigger, Dashboard, Widget, Input, Output, and Function
  configuration semantics belong to the relevant feature/configuration skill,
  not installation operations, unless the issue is service/database/runtime
  layout.

## Bundled Files

Read or run these bundled files instead of looking up upstream material:

- [references/installation-operations.md](references/installation-operations.md)
  — read for installation prerequisites, first-login checks, operational command
  patterns, InfluxDB measurement database notes, and dependency-page behavior.
- [references/service-layout.md](references/service-layout.md) — read when a task
  asks where Mycodo stores services, logs, databases, backups, certificates,
  sockets, symlinks, custom modules, or runtime files.
- [references/backup-upgrade-restore.md](references/backup-upgrade-restore.md)
  — read before any backup, restore, export/import, upgrade, post-upgrade, or
  database-version repair action.
- [references/docker-deployment.md](references/docker-deployment.md) — read for
  experimental Docker deployment constraints, compose services, volumes, ports,
  time zone settings, Grafana/Telegraf, and local-service conflicts.
- [references/troubleshooting.md](references/troubleshooting.md) — read when the
  web UI is inaccessible, the daemon is stopped, InfluxDB data is missing,
  database version is wrong, install/upgrade/restore logs show errors, or Docker
  does not come up.
- [scripts/check_mycodo_environment.py](scripts/check_mycodo_environment.py) — run
  for a non-mutating environment summary from any directory. It reports Python,
  optional Mycodo config import/parse results, public service/log paths, and
  warnings. It does not prove hardware, systemd, nginx, InfluxDB, Docker, backup,
  restore, or installer behavior.

## Fast Decision Tree

1. **New install on Raspberry Pi OS/Debian**: read
   [installation-operations.md](references/installation-operations.md). Confirm
   the user accepts host/network/package/service mutation before running the
   public install command.
2. **Existing install health check**: run the bundled check script first, then
   inspect service status/logs using [service-layout.md](references/service-layout.md).
3. **Web UI or daemon failure**: read
   [troubleshooting.md](references/troubleshooting.md). Start with logs and
   service status; do not delete databases or restart a live control system until
   the user confirms the operational risk.
4. **Backup, restore, import/export, or upgrade**: read
   [backup-upgrade-restore.md](references/backup-upgrade-restore.md) before any
   command. Treat restore, settings import, upgrade, and database recreation as
   destructive or host-mutating.
5. **Docker**: read [docker-deployment.md](references/docker-deployment.md).
   Docker support is experimental and requires explicit user acceptance of port,
   privileged-device, volume, and compatibility risks.

## Version And Layout Anchors

- The inspected Mycodo release reports `MYCODO_VERSION = 8.17.0` and
  `ALEMBIC_VERSION = 5966b3569c89`.
- The public installed layout normally uses `/opt/Mycodo`.
- The settings database is normally `/opt/Mycodo/databases/mycodo.db`.
- Logs are normally under `/var/log/mycodo`; upgrade logs are normally
  `/var/log/mycodo/mycodoupgrade.log`.
- Backups are normally under `/var/Mycodo-backups`.
- The web UI is served through nginx on ports 80 and 443, proxying to a gunicorn
  Unix socket at `/usr/local/mycodoflask.sock`.
- The daemon Pyro URI is normally `PYRO:mycodo.pyro_server@127.0.0.1:9080`; in
  Docker it targets `mycodo_daemon:9080`.

## Safe Inspection Commands

These commands are read-only or informational, but they may reveal hostnames,
versions, paths, or logs. Ask before running them on a sensitive system.

```bash
python scripts/check_mycodo_environment.py --help
python scripts/check_mycodo_environment.py
python scripts/check_mycodo_environment.py --repo-root /opt/Mycodo --json
```

```bash
systemctl status mycodo mycodoflask nginx --no-pager
journalctl -u mycodo -n 100 --no-pager
journalctl -u mycodoflask -n 100 --no-pager
ls -lah /var/log/mycodo /var/Mycodo-backups
```

```bash
curl -k -I https://127.0.0.1/
curl -sI http://127.0.0.1:8086/ping
```

## Mutating Operations Require Explicit Confirmation

Do not run these without the user's explicit confirmation of target host,
maintenance window, backups, physical safety, and acceptable downtime:

- Public install command: `curl -L https://kizniche.github.io/Mycodo/install | bash`.
- Service restart/stop/start for `mycodo`, `mycodoflask`, `nginx`, `influxdb`,
  `influxd`, or `pigpiod` on a live controller.
- `sudo mycodo-commands upgrade-mycodo`, `backup-restore`, `upgrade-post`,
  InfluxDB recreation, settings import, or database rename/delete.
- Docker `up`, `down`, `system prune`, privileged containers, or stopping a local
  non-Docker install to free ports.
- GPIO/I2C/UART/1-Wire/Bluetooth/camera operations or any change that can switch
  Outputs, PID controllers, Conditional logic, or Triggers affecting hardware.

## First-login Checklist

After a successful install, verify:

1. Open `https://<host-or-ip>/` and create the first admin user.
2. Log in and confirm the displayed time is correct; wrong system time can break
   measurement storage and retrieval.
3. Confirm the host/version text at the top left is green, meaning the daemon is
   running. Yellow/orange/red indicates daemon or connectivity trouble.
4. Confirm browser JavaScript blockers are disabled for the Mycodo web UI.
5. Confirm InfluxDB measurement database settings if the installer skipped local
   InfluxDB or uses a remote server.

## Verification Limits

This sub-skill was produced from CPU/source inspection only. Raspberry Pi
GPIO/I2C/UART/1-Wire/Bluetooth/camera behavior, systemd/nginx/InfluxDB services,
Docker deployment, backup/restore/import/export, upgrade execution, and the full
installer were not run in this production pass. Treat those as live operational
surfaces that require host-specific confirmation before mutation.
