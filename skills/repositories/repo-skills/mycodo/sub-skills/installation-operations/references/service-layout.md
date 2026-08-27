# Service, Path, Database, And Log Layout

Read this when diagnosing an installed Mycodo host, mapping logs to failures, or deciding whether a command touches runtime state. Paths below describe the public installed layout; a source checkout may differ.

## Core installed layout

| Surface | Conventional path or name | Notes |
| --- | --- | --- |
| Install root | `/opt/Mycodo` | Main application tree used by installer and examples. |
| Python environment | `/opt/Mycodo/env` | Use installed `mycodo-python`/`mycodo-pip` symlinks when available instead of guessing. |
| Settings database | `/opt/Mycodo/databases/mycodo.db` | SQLite database for settings, users, controllers, modules, and configuration. |
| Alembic migrations | `/opt/Mycodo/alembic_db` | Database migration scripts and current Alembic version. |
| Measurement DB | InfluxDB, usually host `127.0.0.1`/`localhost`, port `8086` | Stores time-series measurements; can be local 1.x, local 2.x, Docker service, or remote. |
| Backups | `/var/Mycodo-backups` | Created during upgrades or from Backup Restore page. |
| Logs | `/var/log/mycodo` | Mycodo application logs; nginx logs live under `/var/log/nginx`. |
| Cameras | `/opt/Mycodo/cameras` | Camera captures/timelapse data when enabled. |
| Notes attachments | `/opt/Mycodo/note_attachments` | Files attached to notes. |
| User scripts | `/opt/Mycodo/mycodo/user_scripts` | User-created scripts; treat execution as potentially unsafe. |
| User Python code | `/opt/Mycodo/mycodo/user_python_code` | Python-code Input/Output content; may execute arbitrary user code. |

## Services and processes

| Service/process | Purpose | Safe first checks |
| --- | --- | --- |
| `mycodo` / `mycodo_daemon.py` | Daemon that runs Inputs, Outputs, Functions, PID, Conditional, Trigger, Actions, and Pyro API. | Web UI top-left version indicator, `systemctl status mycodo`, daemon log. |
| `mycodoflask` | Gunicorn/Flask web application. | `systemctl status mycodoflask`, frontend log, nginx error log. |
| `nginx` | HTTPS reverse proxy for the web UI/API. | `systemctl status nginx`, `curl -k -I https://127.0.0.1/`, nginx logs. |
| `influxdb`/`influxd` | Measurement time-series database when local. | `curl -sI http://127.0.0.1:8086/ping`, InfluxDB service status. |
| `pigpiod` | GPIO daemon for pigpio-backed modules when enabled. | Check only if a selected device requires pigpio. |

Restarting `mycodo` can stop or restart environmental control. Restarting `mycodoflask` affects web/API availability. Restarting `nginx` affects web/API TLS access. Restarting InfluxDB can interrupt measurement storage. Ask before restarting a live controller.

## Log files

Common log files under `/var/log/mycodo` include:

- `mycodo.log` — daemon/controller log; primary place for Input/Output/Function/PID/Action failures.
- `mycodokeepup.log` — daemon keepalive/supervision log.
- `mycodobackup.log` — backup log.
- `mycododependency.log` — dependency-install log.
- `mycodoimport.log` — import log.
- `mycodoupgrade.log` — upgrade log; first stop for post-upgrade UI failures.
- `mycodorestore.log` — restore log.
- `login.log` — login/auth-related messages.

Nginx access/error logs are usually `/var/log/nginx/access.log` and `/var/log/nginx/error.log`.

## Safe status probes

```bash
systemctl status mycodo mycodoflask nginx --no-pager
journalctl -u mycodo -n 100 --no-pager
journalctl -u mycodoflask -n 100 --no-pager
ls -lah /var/log/mycodo /var/Mycodo-backups
curl -k -I https://127.0.0.1/
curl -sI http://127.0.0.1:8086/ping
```

Use `sudo` only when the host requires it for status/log access. Do not combine these with restarts, upgrade, restore, or dependency installation in a single opaque command.

## Daemon/API connectivity anchors

- Local Pyro URI: `PYRO:mycodo.pyro_server@127.0.0.1:9080`.
- Docker Pyro URI: `PYRO:mycodo.pyro_server@mycodo_daemon:9080`.
- REST API docs on an installed host: `https://<host>/api`.
- API media type for v1: `application/vnd.mycodo.v1+json`.

Use `api-and-automation` for REST/Pyro command semantics; this reference only maps where services live and how to inspect them safely.

## Service configuration details

The public installed service files use these important anchors:

- `mycodo.service` starts the daemon with `/opt/Mycodo/env/bin/python /opt/Mycodo/mycodo/mycodo_daemon.py`, stops with `mycodo_client.py -t`, restarts on failure, waits 20 seconds between restarts, and is wanted by `multi-user.target`.
- `mycodoflask.service` runs from `/opt/Mycodo/mycodo` as gunicorn with one worker, `gthread`, two threads, timeout `300`, PID `/var/run/mycodoflask.pid`, and Unix socket `/usr/local/mycodoflask.sock`.
- nginx listens on `80` and `443 ssl`, uses certs under `/opt/Mycodo/mycodo/mycodo_flask/ssl_certs`, and proxies to `http://unix:/usr/local/mycodoflask.sock`.
- The nginx site permits large requests for uploads/imports and has a Mycodo-provided `502` error page. If the UI shows a gateway error, inspect nginx and `mycodoflask` before touching databases.
- pigpiod service variants use sample rates `-s 1` (low latency) and `-s 5` (high latency). Enabling or changing pigpiod is hardware-facing and requires user confirmation.

## Logrotate details

The installed logrotate config applies to `/var/log/mycodo/*.log`, rotates hourly when logs reach about 10 MB, keeps 5 rotations, compresses with delay, skips empty/missing logs, creates files as `mycodo:mycodo` mode `644`, and uses `copytruncate`. If a log appears short, check rotated compressed files before assuming history is absent.

## Verification limits

These paths and service details were distilled from static files and configuration. The production pass did not run systemd, nginx, InfluxDB, Docker, backup/restore, upgrade, installer, or Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera checks.
