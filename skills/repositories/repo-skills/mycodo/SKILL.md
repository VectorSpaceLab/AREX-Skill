---
name: mycodo
description: "Use Mycodo for Raspberry Pi environmental regulation,
  sensor/actuator control, PID workflows, custom modules, APIs, operations, and
  source maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Mycodo Repo Skill

Use this repo skill when a task involves Mycodo, an open source Raspberry Pi /
Debian environmental regulation system that couples Inputs and Outputs through
Functions, Actions, Widgets, Dashboards, PID controllers, Conditional logic,
Triggers, InfluxDB-backed measurements, REST/Pyro automation, and custom module
extension points.

## Start Here

1. Identify whether the user is working with an **installed Mycodo host**, a
   **source checkout**, or a **planned design**.
2. Confirm safety before any operation that can mutate services, databases,
   Docker containers, dependencies, hardware buses, Outputs, PID/Conditional
   logic, backups, restores, imports, upgrades, or API credentials.
3. Route to the smallest sub-skill below and read its references before writing
   commands or code.
4. Use bundled scripts with `--help` first. They are safe by default and replace
   source-checkout scripts/examples that would otherwise be runtime dependencies.
5. For live installations, verify the installed Mycodo version and live `/api`
   docs because this skill was generated from Mycodo 8.17.0.

## Sub-skill Routes

- [installation-operations](sub-skills/installation-operations/SKILL.md) — use
  for installation, first login, services, nginx, InfluxDB, logs, backup,
  restore, import/export, upgrade, Docker, and deployed-host troubleshooting.
- [devices-and-control](sub-skills/devices-and-control/SKILL.md) — use for
  Inputs, Outputs, Functions, Actions, Widgets, Dashboards, PID, Conditional,
  Trigger, setpoint tracking, cameras, notes, energy, hardware choices, and
  control-workflow troubleshooting.
- [custom-modules](sub-skills/custom-modules/SKILL.md) — use for writing,
  validating, importing, updating, or debugging custom Inputs, Outputs,
  Functions, Actions, and Widgets.
- [api-and-automation](sub-skills/api-and-automation/SKILL.md) — use for HTTPS
  REST API calls, API keys, endpoint families, multi-channel measurements,
  local Pyro `DaemonControl`, `mycodo-client`, and automation safety.
- [development-and-testing](sub-skills/development-and-testing/SKILL.md) — use
  for source navigation, Flask/API/database changes, Alembic migrations,
  software tests, manual hardware-test classification, docs generation, and
  maintainer workflows.

## Repo-level References And Scripts

- [references/package-facts.md](references/package-facts.md) — read for the
  compact capability map, verified version/signature facts, and verification
  boundaries.
- [references/troubleshooting.md](references/troubleshooting.md) — read when a
  problem spans install/runtime, control, custom modules, API automation, or
  source maintenance.
- [references/repo-provenance.md](references/repo-provenance.md) — read before
  deciding whether this skill is current for a checkout or target installation.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  — structured metadata consumed by managed repo-skill import/router tooling.
- [scripts/quick_mycodo_probe.py](scripts/quick_mycodo_probe.py) — run as a
  non-mutating package/source probe when a Python environment or checkout is
  available.

## Minimal Install/Import Checks

For a live host or new deployment, use `installation-operations` for the public
quick-install path that targets `/opt/Mycodo`. Running the installer mutates
packages, services, users, nginx, and possibly InfluxDB; route there and ask
before executing it.

For source or package inspection only:

```bash
python scripts/quick_mycodo_probe.py --help
python scripts/quick_mycodo_probe.py --repo-root /path/to/Mycodo
```

Expected Mycodo version for this skill snapshot: `8.17.0`.

## High-safety Operations

Require explicit user confirmation before:

- public installer or dependency installation,
- service restarts/stops/starts,
- Docker `up/down/prune`,
- backup/restore/import/export/upgrade or settings database changes,
- GPIO/I2C/UART/1-Wire/Bluetooth/camera/manual hardware tests,
- Output/PID/Trigger/Conditional/Action commands,
- REST/Pyro/API calls that mutate state,
- exposure of API keys, logs, backups, camera images, or historical measurements.

## Verification Limits

This skill was produced from Mycodo source, docs, tests, and CPU Python
inspection. It did not execute the installer, systemd/nginx/InfluxDB services,
Docker deployment, backup/restore/import/export/upgrade, live REST calls,
manual hardware tests, or physical GPIO/I2C/UART/1-Wire/Bluetooth/camera
operations. Treat those as target-host checks, not proven runtime facts.
