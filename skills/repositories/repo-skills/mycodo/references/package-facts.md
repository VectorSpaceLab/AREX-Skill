# Mycodo Package Facts

Read this for compact verified facts before using the root router or deciding whether a task belongs to a sub-skill.

## Identity and purpose

- Public project name: Mycodo.
- Inspected version: `8.17.0`.
- Purpose: open source environmental regulation software for Raspberry Pi or similar Debian-based systems. It couples Inputs and Outputs through Functions, Actions, Dashboards, PID, Conditional logic, Triggers, and other controllers.
- Primary deployment target: Raspberry Pi OS 13 Trixie or another Debian-based Linux system with an active internet connection; Raspberry Pi 3/4/5 are the recommended SBCs.
- Main package/import roots: `mycodo` and `alembic_db` in a source or installed tree.

## Main capability families

| Family | What it covers | Owning sub-skill |
| --- | --- | --- |
| Install/operate | Bare-metal install, services, nginx, InfluxDB, Docker, backups, upgrades, logs | `installation-operations` |
| Device/control setup | Inputs, Outputs, PID, Conditional, Trigger, Actions, Widgets, Dashboards, cameras, notes, energy | `devices-and-control` |
| Custom modules | Custom Input/Output/Function/Action/Widget source contracts and validation | `custom-modules` |
| Automation APIs | HTTPS REST API, multi-channel measurement endpoint, Pyro `DaemonControl`, `mycodo-client` | `api-and-automation` |
| Maintainer work | Source layout, Flask API, DB migrations, software tests, docs generation, translations | `development-and-testing` |

## Verified live-inspection facts

CPU/source inspection verified these Python facts:

```python
from mycodo.mycodo_client import DaemonControl
DaemonControl(pyro_uri='PYRO:mycodo.pyro_server@127.0.0.1:9080', pyro_timeout=None)
```

Selected method signatures:

- `output_on(output_id, output_type=None, amount=0.0, min_off=0.0, output_channel=None, trigger_conditionals=True)`
- `output_off(output_id, output_channel=None, trigger_conditionals=True)`
- `output_on_off(output_id, state, output_type=None, amount=0.0, output_channel=None)`
- `input_force_measurements(input_id)`
- `pid_pause(pid_id)`, `pid_resume(pid_id)`, `pid_set(pid_id, setting, value)`

The REST API uses HTTPS, API keys, and API v1 media type `application/vnd.mycodo.v1+json`. Installed endpoint documentation is served at `/api` on a running Mycodo host.

## Verification boundaries

This repo skill was built from source/docs/tests plus a private CPU inspection environment. It did **not** execute:

- the public installer,
- systemd/nginx/InfluxDB services,
- Docker compose,
- backup/restore/import/export/upgrade actions,
- GPIO/I2C/UART/1-Wire/Bluetooth/camera/manual hardware tests,
- live REST calls requiring API keys.

Those capabilities are documented with safety gates and require target-host verification before mutation or physical actuation.
