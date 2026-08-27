# Installation And Operations Troubleshooting

Read this when an installed Mycodo host fails to load, services are unhealthy, measurement storage is missing, or an install/upgrade/restore/import operation fails.

## Triage order

1. Identify whether this is bare-metal or Docker and whether it is safe to interrupt control.
2. Collect version, OS, architecture, install path, and recent change: install, upgrade, restore, import, dependency install, Docker rebuild, service restart, hardware change.
3. Inspect logs before retrying: `/var/log/mycodo`, `/var/log/nginx/error.log`, and relevant service journals.
4. Prefer read-only probes first. Ask before service restarts, database edits, dependency installs, Docker cleanup, restore, or upgrade.

## Common failures

| Symptom or error | Likely causes | Recovery |
| --- | --- | --- |
| Browser cannot reach `https://<host>/` | nginx down, certificate/TLS prompt ignored, wrong host/IP, local and Docker installs conflicting, firewall/port issue | `systemctl status nginx mycodoflask`; `curl -k -I https://127.0.0.1/`; inspect nginx error log; confirm Docker/local port ownership |
| Top-left version/host text is red/orange | daemon inactive, Pyro communication failure, daemon crashed during controller init | inspect daemon log and `systemctl status mycodo`; do not restart on live hardware until safe state confirmed |
| UI inaccessible after upgrade | failed post-upgrade script, DB migration/version issue, frontend crash | inspect `/var/log/mycodo/mycodoupgrade.log`; only after approval consider `sudo mycodo-commands upgrade-post` on the installed host |
| Incorrect database version | Alembic/settings DB mismatch after upgrade/restore/import | inspect upgrade log and System Information; avoid DB rename unless user accepts fresh configuration |
| Graphs empty but Inputs are active | InfluxDB not running/configured, wrong time, measurement DB import without settings IDs, remote DB credentials wrong | check system time, InfluxDB `/ping`, measurement DB settings, controller IDs, and import pairing |
| Dependency page asks repeatedly | optional device dependency install failed, apt/pip/network error, wrong architecture | inspect dependency log; install only the selected device's dependency, not all optional device deps |
| Backup/restore fails | wrong backup path, permissions, incompatible version, DB/service still active | inspect backup/restore logs; verify major version compatibility; stop only with approval |
| Docker starts but hardware does not work | missing device passthrough/permissions, unsupported hardware in containers | verify container device access and host modules; treat as Docker/hardware limitation |
| `mycodo-client` times out | daemon/Pyro unavailable or wrong URI/timeout | use `api-and-automation` troubleshooting; check daemon status before retrying |

## Commands that are not troubleshooting-only

These commands mutate state. Do not use them as a first diagnostic step:

```bash
sudo service mycodo restart
sudo service mycodoflask restart
sudo mycodo-commands upgrade-mycodo
sudo mycodo-commands backup-restore <backup>
docker compose down
docker system prune -a
mv /opt/Mycodo/databases/mycodo.db /opt/Mycodo/databases/mycodo.db.backup
```

If the user approves a mutating recovery, record the current logs and backup state first. For incorrect database version, prefer upgrade-log/post-upgrade diagnosis before the last-resort database rename; the rename starts a fresh settings configuration and can orphan configured Inputs, Outputs, Functions, Actions, Widgets, Dashboards, PID, Conditional rules, and Triggers from the active UI.

## Extra concrete recovery checks

- Install failed: read `/opt/Mycodo/install/setup.log`; verify Python >=3.8, internet, apt/pip availability, `dialog`, and whether `/opt/Mycodo` already existed.
- Web UI 502: inspect nginx error log, `mycodoflask` status, and `/usr/local/mycodoflask.sock`; do not touch SQLite first.
- Daemon stopped: inspect `/var/log/mycodo/mycodo.log` for custom module, dependency, database, or hardware-bus errors before restart.
- Graphs empty: verify system time, InfluxDB `/ping`, measurement database settings, and whether measurement import had matching settings IDs.
- Restore failed: inspect `/var/log/mycodo/mycodorestore.log`, `/opt/Mycodo`, `/var/Mycodo-backups`, and `/var/mycodo-root` before retrying.

## When to stop

Stop and ask for live-system confirmation when the next step could turn physical Outputs on/off, pause regulation, wipe settings, overwrite backups, delete Docker images, install system packages, expose API keys, or require private hardware access.
