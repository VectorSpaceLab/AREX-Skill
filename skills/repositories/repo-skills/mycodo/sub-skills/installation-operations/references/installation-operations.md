# Installation And Operations

This reference covers public installation and daily operations for Mycodo. Treat
all installer, package, service, database, network, and Docker actions as live
host mutations unless explicitly described as inspection only.

## Scope Boundaries

Use this reference for Mycodo deployment and runtime health. Route custom module
authoring to `custom-modules`, REST/Pyro automation to `api-and-automation`, and
source checkout maintenance or code testing to `development-and-testing`.

## Supported/Expected Platform

- Mycodo 8.17.0 is open source environmental regulation software designed for a
  Raspberry Pi or similar Linux system that couples Inputs and Outputs through
  Functions, Actions, Widgets, Dashboards, PID, Conditional logic, and Triggers.
- The documented bare-metal install target is a Debian-based operating system,
  tested with Raspberry Pi OS 13 Trixie.
- Recommended hardware is a Raspberry Pi 3, 4, or 5 with GPIO pins. Raspberry Pi
  Zero, 1, and 2 are no longer recommended.
- Mycodo has been described as working on Raspberry Pi OS 13 Lite/Desktop,
  32-bit and 64-bit.
- The installer requires an active internet connection and Python 3.8 or newer.
- The full installer was not run during skill production; validate on the target
  host before treating installation as proven.

## Public Install Workflow

The public quick-install command installs to `/opt/Mycodo` and is destructive in
the sense that it installs apt packages, configures services, creates users and
symlinks, configures nginx, and may install/configure InfluxDB:

```bash
curl -L https://kizniche.github.io/Mycodo/install | bash
```

Before running it, confirm:

1. The user selected the intended host and accepts package/network/service
   changes.
2. Any old `/opt/Mycodo` installation is intentionally being kept, moved, or
   removed. The installer expects `/opt/Mycodo` as the installed layout and aborts
   if it detects a conflicting install while run from another location.
3. The host has internet access for apt, pip, release downloads, InfluxDB, and
   supporting packages.
4. A maintenance window is acceptable; environmental control Outputs should be in
   a safe state before installation or service restarts.

The interactive installer asks for license acceptance, interface language, and
InfluxDB choice. Its install log is written to `/opt/Mycodo/install/setup.log`.
If an install fails, inspect the end of that log before retrying.

## InfluxDB Install Choice

Mycodo stores measurements in InfluxDB. The installer offers different options by
architecture:

- 32-bit/`armhf`: InfluxDB 1.x or no local InfluxDB.
- 64-bit ARM or x86_64: InfluxDB 2.x recommended, InfluxDB 1.x old, or no local
  InfluxDB.
- If no local InfluxDB is installed, configure the measurement database host,
  port, database/bucket, retention policy, and credentials in Mycodo settings
  after installation.

Operational assumptions distilled from the code:

- The conventional measurement database/bucket name is `mycodo_db`.
- The conventional local InfluxDB port is `8086`.
- Mycodo checks configured settings first, then can probe local hosts such as
  `localhost`, `127.0.0.1`, and Docker service host `mycodo_influxdb`.
- `/ping` should return an InfluxDB response with version headers when reachable.
- Do not recreate/drop InfluxDB measurement data unless the user confirms the
  data-loss risk and a backup/export plan.

Safe read-only probes:

```bash
curl -sI http://127.0.0.1:8086/ping
curl -sI http://localhost:8086/ping
```

## First Login And Web UI Validation

After an apparently successful install:

1. Browse to `https://<host-or-ip>/`. Self-signed certificates are expected on a
   local install.
2. Create the first admin user when prompted, then log in.
3. Check that system time displayed in the web UI is correct. Incorrect time can
   cause measurement storage and graph retrieval problems.
4. Confirm the host/version text at the top left is green. Green means daemon
   running; yellow/orange/red points to daemon or communication trouble.
5. Disable browser JavaScript-blocking extensions for the Mycodo web UI.
6. If the installer skipped InfluxDB or uses a remote InfluxDB server, configure
   measurement database settings before expecting graphs to populate.

## Daily Operational Checks

Read-only checks that usually do not affect control state:

```bash
systemctl status mycodo mycodoflask nginx --no-pager
journalctl -u mycodo -n 100 --no-pager
journalctl -u mycodoflask -n 100 --no-pager
ls -lah /var/log/mycodo
ls -lah /var/Mycodo-backups
curl -k -I https://127.0.0.1/
```

Treat restarts as mutating because the daemon controls Inputs, Outputs,
Functions, PID, Conditional logic, Triggers, and Actions:

```bash
sudo service mycodo restart
sudo service mycodoflask restart
sudo service nginx restart
```

Ask for explicit approval before using restart commands on a live environment.

## Dependency Operations

Mycodo has a web UI dependency page at `[Gear Icon] -> Dependencies`. Normal use
does not require manual dependency installation. When adding an Input, Output,
Function, or other device with unmet dependencies, Mycodo prompts to install what
that device needs.

Operational guidance:

- Prefer the web UI dependency prompt over ad-hoc package commands.
- Record which Input, Output, Function, Action, or Widget requested the
  dependency.
- Stop before installing hardware-specific dependencies, enabling GPIO/I2C/UART,
  or modifying camera/Bluetooth/1-Wire behavior unless the user confirms the
  target hardware and physical risk.

## Useful Installed Commands

The installer creates convenient symlinks when initialization succeeds:

- `mycodo-commands` — administrative command dispatcher for backup, restore,
  upgrade, service, dependency, web server, InfluxDB, and permissions operations.
- `mycodo-client` — local daemon client; use `api-and-automation` for command
  semantics.
- `mycodo-daemon` — daemon entry point.
- `mycodo-python` and `mycodo-pip` — Python/pip from the Mycodo virtualenv.
- `mycodo-backup` and `mycodo-restore` — backup/restore entry points.

Use `sudo mycodo-commands` without an action to view available installed actions.
Do not run actions from this list without classifying whether they mutate host,
network, services, databases, or hardware.

## Operational Data To Collect Before Escalation

When reporting or escalating an operational issue, collect:

- Mycodo version and expected database migration version from the web UI System
  Information page or the bundled environment check.
- Host OS, CPU architecture, Python version, and whether this is Docker or
  bare-metal.
- Whether InfluxDB is local 1.x, local 2.x, remote, or skipped.
- Current status of `mycodo`, `mycodoflask`, `nginx`, and InfluxDB services.
- Last 100-300 lines of relevant Mycodo logs from `/var/log/mycodo` and nginx
  errors from `/var/log/nginx/error.log`.
- Whether the failure began after install, upgrade, restore, settings import,
  measurement import, dependency installation, or hardware changes.

## Verification Limits

CPU/source inspection confirmed configuration constants and installer/service
layout. It did not execute the installer, run systemd/nginx/InfluxDB, operate
Docker, perform backup/restore/import/export, or exercise Raspberry Pi
GPIO/I2C/UART/1-Wire/Bluetooth/camera hardware.
