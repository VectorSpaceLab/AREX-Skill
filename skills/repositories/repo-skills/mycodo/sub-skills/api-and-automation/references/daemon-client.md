# DaemonControl, Pyro, And `mycodo-client`

Use this reference when automation runs on the Mycodo host and needs to talk to
the local daemon instead of the remote HTTPS REST API.

## When To Use Local Daemon Access

Use `DaemonControl` or `mycodo-client` when:

- The code runs on the same trusted host as the Mycodo daemon.
- You need daemon operations that are not exposed as stable REST endpoints, such
  as Function Action execution, Widget helpers, PID setting changes, or direct
  Output/PID/Input commands.
- You need Python return values from daemon methods and can import Mycodo's
  installed package.
- A shell script or maintenance command must interact with the daemon locally.

Use REST instead when:

- The caller is remote or language-neutral.
- The operation is covered by a documented HTTPS endpoint.
- You want API-key authentication and web UI permissions rather than local host
  trust/Pyro access.

Do not expose the Pyro port as a public remote API. It is a local daemon control
surface, not an HTTPS-authenticated web API.

## DaemonControl Construction

The daemon client class is:

```python
from mycodo.mycodo_client import DaemonControl

control = DaemonControl(
    pyro_uri="PYRO:mycodo.pyro_server@127.0.0.1:9080",
    pyro_timeout=None,
)
```

Constructor parameters:

- `pyro_uri`: Pyro5 URI for the Mycodo daemon. Default resolves to the Mycodo
  configuration constant and is commonly
  `PYRO:mycodo.pyro_server@127.0.0.1:9080`.
- `pyro_timeout`: optional timeout. If omitted, Mycodo tries to read the daemon
  timeout from its SQL settings and falls back to 30 seconds if that lookup
  fails.

Safe daemon probe:

```python
from mycodo.mycodo_client import DaemonControl

control = DaemonControl(pyro_timeout=10)
result = control.check_daemon()
print(result)  # "GOOD" means reachable/healthy in the helper path.
```

If import fails, run the code with the installed Mycodo Python environment. A
common installed layout is `/opt/Mycodo/env/bin/python`, but follow the user's
actual installation.

## Important Method Families

### Status And Daemon

```python
control.check_daemon()        # Returns "GOOD" or an error string.
control.daemon_status()       # Daemon status, commonly "alive" when running.
control.is_in_virtualenv()    # Whether daemon reports running in a virtualenv.
control.ram_use()             # Daemon RAM use.
control.terminate_daemon()    # Disruptive; require explicit authorization.
```

### Controller Activation

```python
control.controller_is_active(controller_id)
control.controller_activate(controller_id)
control.controller_deactivate(controller_id)
control.controller_restart(controller_id)
```

Use controller unique IDs, not display names. Confirm whether the target is an
Input, Output, PID, Conditional, Trigger, or Function before activation changes.

### Inputs

```python
control.input_force_measurements(input_id)
```

This instructs an Input to conduct a measurement. It may touch hardware buses or
sensors, so confirm the Input and timing before use. The method catches daemon
exceptions and can return a tuple whose first element indicates failure.

### Outputs

Verified call signatures:

```python
control.output_on(
    output_id,
    output_type=None,
    amount=0.0,
    min_off=0.0,
    output_channel=None,
    trigger_conditionals=True,
)

control.output_off(
    output_id,
    output_channel=None,
    trigger_conditionals=True,
)

control.output_on_off(
    output_id,
    state,
    output_type=None,
    amount=0.0,
    output_channel=None,
)

control.output_sec_currently_on(output_id, output_channel=None)
control.output_setup(action, output_id)  # action: Add, Delete, Modify
control.output_state(output_id, output_channel)
control.output_states_all()
```

Automation rules:

- Always confirm `output_id` and `output_channel`; channels are typically
  zero-based.
- Use `output_type="sec"` plus `amount=<seconds>` for timed on/off Outputs.
- Use `output_type="pwm"` plus `amount=<0-100 duty cycle>` for PWM.
- Use `output_type="vol"` plus `amount=<volume>` for volume-type Outputs.
- Leave `trigger_conditionals=True` unless the user specifically wants to avoid
  Conditional/Trigger reactions to state changes.
- Do not actuate Outputs without understanding the connected hardware.

### PID

```python
control.pid_pause(pid_id)
control.pid_hold(pid_id)
control.pid_resume(pid_id)
control.pid_mod(pid_id)
control.pid_get(pid_id, setting)
control.pid_set(pid_id, setting, value)
```

Supported `pid_get` settings include `setpoint`, `error`, `integrator`,
`derivator`, `kp`, `ki`, and `kd`. Supported `pid_set` settings include
`setpoint`, `method`, `integrator`, `derivator`, `kp`, `ki`, and `kd`.

PID changes can affect climate, dosing, heating, cooling, or other controlled
systems. Require explicit user confirmation of the PID unique ID, setting, new
value, safety envelope, and rollback plan before `pid_set`, `pid_pause`,
`pid_hold`, or `pid_resume`.

### Function Actions

```python
control.trigger_action(action_id, value={}, debug=False)
control.trigger_all_actions(function_id, message='', debug=False)
```

`trigger_action` executes a Function Action. The optional `value` dict should at
least be able to carry a `message` key when the action appends messages. Confirm
Action/Function IDs and side effects before triggering; Actions may send email,
change Outputs, call webhooks, or mutate local state.

### Conditional, Trigger, Misc Settings Refresh

```python
control.refresh_daemon_conditional_settings(unique_id)
control.refresh_daemon_trigger_settings(unique_id)
control.refresh_daemon_misc_settings()
```

Use after settings changes when the daemon must reload runtime state. Avoid
refresh loops; investigate why a controller is stale.

### Display, Widget, And Email Helpers

```python
control.lcd_backlight(lcd_id, state)
control.lcd_flash(lcd_id, state)
control.lcd_reset(lcd_id)
control.display_backlight_color(lcd_id, color)
control.widget_add_refresh(unique_id)
control.widget_remove(unique_id)
control.widget_execute(unique_id)
control.send_email(recipients, message, subject='')
```

Displays, Widgets, Dashboards, and email actions are user-visible. Confirm IDs,
privacy expectations, and notification side effects before use.

### Module Function

```python
control.module_function(
    controller_type,
    unique_id,
    button_id,
    args_dict,
    thread=True,
    return_from_function=False,
    timeout=None,
)
```

Use only when you know the controller module's button/function contract. This is
more module-specific than the generic REST surfaces. Require user confirmation
because it can trigger arbitrary module behavior.

## `mycodo-client` CLI

`mycodo-client` is the shell command for communicating with the daemon. Run
`mycodo-client --help` on the Mycodo host to confirm the installed command and
option set.

Common low-risk probes:

```bash
mycodo-client --help
mycodo-client --checkdaemon
mycodo-client --ramuse
```

Input and Output examples that require confirmed IDs:

```bash
mycodo-client --input_force_measurements <input_id>
mycodo-client --output_state <output_id> --output_channel 0
mycodo-client --output_currently_on <output_id> --output_channel 0
```

Output actuation examples; use only after explicit authorization:

```bash
mycodo-client --outputon <output_id> --output_channel 0 --duration 10
mycodo-client --outputon <output_id> --output_channel 0 --dutycycle 50
mycodo-client --outputoff <output_id> --output_channel 0
```

PID CLI options include:

```bash
mycodo-client --pid_pause <pid_id>
mycodo-client --pid_hold <pid_id>
mycodo-client --pid_resume <pid_id>
mycodo-client --pid_get_setpoint <pid_id>
mycodo-client --pid_get_error <pid_id>
mycodo-client --pid_get_integrator <pid_id>
mycodo-client --pid_get_derivator <pid_id>
mycodo-client --pid_get_kp <pid_id>
mycodo-client --pid_get_ki <pid_id>
mycodo-client --pid_get_kd <pid_id>
mycodo-client --pid_set_setpoint <pid_id> <setpoint>
mycodo-client --pid_set_integrator <pid_id> <integrator>
mycodo-client --pid_set_derivator <pid_id> <derivator>
mycodo-client --pid_set_kp <pid_id> <kp>
mycodo-client --pid_set_ki <pid_id> <ki>
mycodo-client --pid_set_kd <pid_id> <kd>
```

For PID hold/resume/set automation where correctness matters, prefer direct
`DaemonControl` calls so the Python method, return value, and exception handling
are explicit.

Function Action examples; use only after confirming effects:

```bash
mycodo-client --trigger_action <action_id>
mycodo-client --trigger_all_actions <function_id>
```

Disruptive command:

```bash
mycodo-client --terminate
```

Do not terminate the daemon unless the user explicitly requests it and accepts
service interruption.

## REST Versus DaemonControl Decision Table

| Need | Prefer | Reason |
|---|---|---|
| Remote app/mobile/dashboard client | REST | HTTPS/API-key access from outside the host. |
| Bulk latest sensor values | REST `/api/measurements/multi` | One request for many channels. |
| Local one-shot shell maintenance | `mycodo-client` | Installed command is simple for operators. |
| Programmatic Python daemon operation | `DaemonControl` | Direct return values and explicit methods. |
| Output/PID actuation from a remote client | REST if endpoint exists; otherwise do not expose Pyro | Keep auth/TLS boundary. |
| Function Action execution from local automation | `DaemonControl` or `mycodo-client` | REST route is not listed for action execution. |
| Widget helper calls | `DaemonControl` | Widget helpers are local daemon methods. |
| Dashboard layout edits | Web UI/manual process | No dedicated REST namespace was present in the inspected API surface. |

## Pyro Troubleshooting Quick Checks

1. Confirm code is running on the Mycodo host with the installed Mycodo Python
   environment.
2. Run `mycodo-client --checkdaemon` or `DaemonControl(pyro_timeout=10).check_daemon()`.
3. If you see `Pyro5 TimeoutError`, check daemon load, timeout, and whether the
   requested method is blocking on hardware.
4. If you see `Pyro5 CommunicationError`, check that the daemon and Pyro server
   are running and reachable at the configured URI.
5. If you see `Failed to locate Pyro5 Nameserver`, confirm the URI and daemon
   startup path.
6. Stop before restarting services, changing systemd/nginx/InfluxDB, or editing
   installation files unless the user authorizes system mutation.
