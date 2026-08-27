---
name: devices-and-control
description: "Configure Mycodo environmental-control workflows using Inputs,
  Outputs, Functions, Actions, Widgets, Dashboards, PID, Conditional, Trigger,
  Methods, cameras, energy, and notes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Mycodo Devices And Control

Use this sub-skill when a task asks how to configure Mycodo environmental
control from the web UI: Inputs, Outputs, Functions, Actions, Widgets,
Dashboards, measurements, PID, Conditional, Trigger, Methods, camera capture,
energy accounting, notes, or hardware/module selection. This skill is
self-contained; do not reopen repository docs, examples, or tests to use it at
runtime.

## What This Sub-skill Owns

- Planning measurement flows from an Input or Function into InfluxDB and then
  into Widgets, Dashboards, Functions, PID, Conditional, Trigger, energy usage,
  and notes.
- Choosing and configuring built-in Inputs, Outputs, Functions, Actions, and
  Widgets from Mycodo's module families.
- PID regulation, PID Autotune, Bang-Bang control, Conditional Python logic,
  Trigger events, Methods, and setpoint tracking.
- Output actuation choices: on/off duration, PWM duty cycle, volume/pump,
  value/DAC, MQTT, command, remote Mycodo, startup state, shutdown state, and
  Trigger at Startup.
- Input choices: sensor/system/weather/MQTT/TTN/command Inputs, measurement
  units, Period, Pre Output, Power Output power cycling, Input Commands, and
  Input Actions.
- Dashboard design with Widgets, graphs, camera widgets, PID/output controls,
  live measurements, energy reports, and timestamped notes.
- Hardware-aware safety triage for GPIO, I2C, UART, SPI, 1-Wire, Bluetooth,
  cameras, relays, pumps, fans, DACs, ADCs, and optional module dependencies.

## Route Out Of This Sub-skill

- Source-level custom Input, Output, Function, Action, or Widget module authoring
  belongs to `custom-modules`.
- REST API, local Pyro `DaemonControl`, `mycodo-client`, external scripts, or
  remote automation belongs to `api-and-automation`.
- Full installation, upgrades, backup/restore operations, Docker, nginx,
  systemd, InfluxDB service repair, or host service hardening belongs to
  `installation-operations`.
- Repository source-code development, database migrations, Flask routes, and
  upstream test execution are outside this runtime operating skill.

## Bundled Files

Read or run these files instead of looking up upstream material:

- [references/control-workflows.md](references/control-workflows.md) — read when
  designing end-to-end Input → measurement → Output/Function/Action → Dashboard
  workflows, PID/Conditional/Trigger/Method logic, or measurement Max Age
  assumptions.
- [references/hardware-and-control-recipes.md](references/hardware-and-control-recipes.md)
  — read when selecting hardware patterns for chambers, fans, relays, pumps,
  pH/EC dosing, TTN/MQTT, cameras, energy usage, or safe dry-run procedures.
- [references/device-catalog.md](references/device-catalog.md) — read when
  choosing among built-in module families, interfaces, output types, Actions,
  and Widgets without source lookup.
- [references/troubleshooting.md](references/troubleshooting.md) — read when an
  Input has no data, an Output will not actuate, PWM behaves oddly, PID does not
  control, Conditional code errors, Trigger timers miss, widgets show stale
  data, camera/energy/notes fail, or optional dependencies/hardware are absent.
- [scripts/summarize_supported_modules.py](scripts/summarize_supported_modules.py)
  — run only when the user has a Mycodo checkout and wants a static, no-import
  catalog summary from source metadata. Use `--help` first.

## Start Here: Control Planning Loop

1. **Name the goal and risk**: what condition changes, which device can change
   it, and what can be damaged by wrong state, frequency, duration, volume, or
   credentials?
2. **Choose the measurement**: add and activate the Input or Function that
   writes the needed measurement to InfluxDB; set units, Period, and Max Age
   assumptions before adding control logic.
3. **Choose the actuator**: add an Output with the correct type (`on_off`,
   `pwm`, `volume`, or `value`), interface, channel, startup state, shutdown
   state, and energy-current metadata.
4. **Pick the controller**: PID for proportional feedback, Bang-Bang for simple
   hysteresis, Conditional for custom Python decisions, Trigger for events or
   timers, and Method/Setpoint Tracking when the target should change over time.
5. **Attach Actions**: connect Input Actions, Conditional Actions, or Trigger
   Actions to Outputs, PID controls, MQTT, e-mail/photo, notes, logs, or
   controller activation.
6. **Observe first**: create Live Measurements, Dashboard Widgets, graphs, and
   notes before leaving control unattended.
7. **Bound mutation**: require explicit confirmation before changing Outputs,
   PID activation, system restart/shutdown, command Outputs, credentials,
   network endpoints, or any live wiring.

## Minimal Web UI Workflows

### Add An Input Measurement

1. Navigate to `Setup -> Input`.
2. Add the Input family matching the sensor/system source.
3. Set interface/location fields such as GPIO BCM pin, I2C address and bus,
   UART device, FTDI device, 1-Wire serial, Bluetooth adapter, IP/HTTP/MQTT, or
   TTN credentials as required by the module.
4. Set `Period (seconds)` and measurement unit/channel options.
5. If a sample requires a purge fan, pump, or valve, configure `Pre Output`,
   `Pre Output Duration`, and whether it stays on during measurement.
6. If the sensor can recover from power cycling, configure `Power Output` and
   verify the physical circuit can safely switch sensor power.
7. Save, activate, then confirm Live Measurements and graph data before adding
   control logic.

### Add An Output Actuator

1. Navigate to `Setup -> Output`.
2. Choose output type by physical action: On/Off relay, PWM, volume/pump, value
   output, MQTT, command, remote Mycodo, motor, DAC, or expander board.
3. Configure channel options, On State, command strings, duty cycle, flow rate,
   value range, or protocol as appropriate.
4. Set `Startup State` and `Shutdown State`; use `Do Nothing` only when the
   device has an independent safe state.
5. Set `Current Draw (amps)` when energy duration accounting matters.
6. Test with short, supervised `Seconds to turn On`, duty cycle, volume, or
   value commands before connecting loads that can heat, flood, dose, or move.

### Add A Function Controller

- Use **PID** for feedback that should approach and maintain a setpoint with
  proportional/integral/derivative terms. Set `Max Age` so stale measurements do
  not actuate Outputs.
- Use **PID Autotune** only as experimental guidance after a supervised dry run;
  watch the daemon log and graph output during perturbation.
- Use **Bang-Bang** when a simple hysteresis band is sufficient.
- Use **Conditional** when Python logic must combine measurements, Output state,
  controller state, actions, and custom status text.
- Use **Trigger** for Output/PWM state events, edge events, timers, sunrise or
  sunset, and Run PWM Method schedules.
- Use **Methods** for PID setpoint tracking or time-varying PWM duty cycle.

## Safety Checklist Before Activation

- Confirm target controller IDs, channel numbers, units, setpoints, and Max Age
  values from the live web UI.
- Confirm the Output can physically affect the selected measurement and that the
  effect direction (`Raise`, `Lower`, or `Both`) is correct.
- Confirm `Min Off Duration`, `Min/Max On Duration`, duty cycle limits, volume
  limits, or DAC value limits for devices that can be damaged by rapid cycling.
- Confirm command Outputs and Python code cannot leak secrets, erase files,
  restart services, or run untrusted input.
- Confirm MQTT/TTN/API credentials are scoped and not copied into logs or notes.
- Stop and ask the user before mutating GPIO/I2C/UART/1-Wire/Bluetooth/camera,
  system services, nginx, InfluxDB, Docker, backup/restore, or installer state.

## Script Usage

Static source catalog summary from a checkout:

```bash
python scripts/summarize_supported_modules.py --repo-root /path/to/Mycodo --family all --limit 20
```

JSON for integration notes:

```bash
python scripts/summarize_supported_modules.py --repo-root /path/to/Mycodo --json --show-modules
```

The helper only parses Python source text with `ast`; it does not import Mycodo,
load optional dependencies, contact hardware, use credentials, or run daemon
operations.

## Verification Limits

This sub-skill was produced from CPU/source inspection and documentation
inspection only. Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera behavior,
systemd/nginx/InfluxDB services, Docker deployment, backup/restore operations,
and full installer execution were not run. Treat hardware and service claims as
configuration guidance that must be verified on the user's live system before
unsafe mutation.
