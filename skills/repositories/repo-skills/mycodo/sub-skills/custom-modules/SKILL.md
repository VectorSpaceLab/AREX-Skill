---
name: custom-modules
description: "Author, validate, import, update, and troubleshoot Mycodo custom
  Inputs, Outputs, Functions, Actions, and Widgets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Mycodo Custom Modules

Use this sub-skill when the task is to author, review, validate, import,
update, or troubleshoot a Mycodo custom module: Inputs, Outputs, Functions,
Actions, or Widgets. This skill is self-contained; do not reopen repository
source docs, examples, or tests at runtime.

## What This Sub-skill Owns

- Module identity dictionaries and their exact unique/name key conventions.
- Base class inheritance, required class names, and required runtime methods.
- Measurement dictionaries, channel dictionaries, InfluxDB storage assumptions,
  and UI channel option mapping.
- `custom_options`, `custom_channel_options`, `custom_commands`,
  `constraints_pass`, dependency tuples, and import/update validation behavior.
- Web UI import/update consequences: frontend reload, daemon restart conditions,
  active controller implications, Widget HTML regeneration, filename/unique-name
  preservation, and delete blockers.
- Static module validation without importing untrusted code.

## Quick Route

1. **New or revised module contract:** read
   [references/module-contracts.md](references/module-contracts.md).
2. **Need a working pattern:** read
   [references/custom-module-recipes.md](references/custom-module-recipes.md).
3. **Static preflight:** run
   [scripts/validate_custom_module.py](scripts/validate_custom_module.py) before
   uploading a file to the web UI.
4. **Import/update failure, blank UI entry, daemon restart, or measurement
   mismatch:** read [references/troubleshooting.md](references/troubleshooting.md).
5. **Hardware, service, credentials, or network side effects:** stop and ask for
   explicit authorization before changing GPIO/I2C/UART/1-Wire/Bluetooth/camera,
   systemd/nginx/InfluxDB, Docker, package sources, backups, or credentials.

## Kind Selection

- **Input**: reads a sensor, command, API, file, bus, or simulated value and
  stores one or more measurements in InfluxDB. Owns `INPUT_INFORMATION` and
  `InputModule(AbstractInput)` with `initialize()` and `get_measurement()`.
- **Output**: controls a device or command and may store output duration, duty,
  volume, or value measurements. Owns `OUTPUT_INFORMATION` and
  `OutputModule(AbstractOutput)` with `initialize()`, `output_switch()`,
  `is_on()`, and `is_setup()`.
- **Function**: performs periodic logic, status production, calculations, or
  custom controller behavior. Owns `FUNCTION_INFORMATION` and
  `CustomModule(AbstractFunction)` with `initialize()` plus usually `loop()` and
  optional `function_status()`.
- **Action**: adds a callable action to Inputs, Conditional, Trigger, PID, or
  other Function workflows. Owns `ACTION_INFORMATION` and
  `ActionModule(AbstractFunctionAction)` with `initialize()`, `run_action()`,
  and `is_setup()`.
- **Widget**: renders or refreshes Dashboard UI. Owns `WIDGET_INFORMATION`.
  Simple Widgets may set `no_class: True`; class-based Widgets use a Widget
  class such as `WidgetModule(AbstractWidget, threading.Thread)` and implement
  `execute_refresh()` when the Dashboard calls back.

## Minimal Safe Workflow

1. Choose a lower-case unique identifier that will not collide with built-in or
   custom modules of the same kind. Keep it stable across updates.
2. Put the exact required information dictionary at module top level.
3. Define dependency tuples as `('pip-pypi'|'apt'|'internal', name, spec)` only
   when the module truly needs them; otherwise use an explicit empty list.
4. Keep top-level code side-effect free. Mycodo loads uploaded files as Python
   modules during import/update validation, so top-level subprocesses, network
   calls, writes, sleeps, daemon calls, or hardware opens can run too early.
5. Put driver imports and hardware/API connections inside `initialize()` or a
   method guarded by runtime state, not at import time.
6. If the module exposes `custom_options`, define every option as a dictionary
   with stable `id`, supported `type`, default value except for `new_line`, and
   user-facing `name`/`phrase` where the UI should render them.
7. If a button appears in `custom_commands`, implement a method with the same
   id; Mycodo passes command input values as a dictionary.
8. For Inputs and Outputs, ensure `measurements_dict` uses measurement/unit IDs
   that already exist in the target Mycodo database or will be added through
   `[Gear Icon] -> Configure -> Measurements` before import.
9. For Outputs and multi-channel Functions, ensure every `channels_dict` entry
   maps only to measurement channels present in `measurements_dict`.
10. Run the bundled static validator. Treat warnings as a pre-upload review
    checklist, not as a proof that Mycodo will accept or safely run the module.
11. Upload through the kind-specific web UI custom-module page; watch returned
    flash messages and daemon log messages before activating hardware.
12. Activate or execute on a harmless test device/configuration first; do not
    connect critical physical devices until the module has survived dry-run and
    short-duration testing.

## Validator Commands

From this sub-skill directory:

```bash
python scripts/validate_custom_module.py --kind input path/to/custom_input.py
python scripts/validate_custom_module.py --kind output path/to/custom_output.py
python scripts/validate_custom_module.py --kind function path/to/custom_function.py
python scripts/validate_custom_module.py --kind action path/to/custom_action.py
python scripts/validate_custom_module.py --kind widget path/to/custom_widget.py
```

The validator parses AST only. It does not import the module, install
`dependencies_module`, contact Mycodo, inspect InfluxDB, touch hardware, or
prove that live web UI import will succeed.

## Import And Update Consequences

- Import writes the uploaded module under the custom module area using the
  lower-case unique name from the information dictionary and reloads the
  frontend so the web UI scans new modules.
- Input, Function, and Widget update paths validate that the new unique key
  matches the existing module unique key. Upload filename alone is not the
  authority.
- Side-loaded Input, Function, and Widget modules can be updated in place when
  Mycodo's parser knows their actual file path; update preserves that original
  filename rather than creating a new name-derived file.
- Updating an active Input or active Function restarts the daemon after the
  frontend reload. Updating a Widget that exists on a Dashboard regenerates
  Widget HTML, reloads the frontend, and restarts the daemon.
- Delete is blocked while existing Input, Output, Function, Action, or Widget
  entries still use that module. Deactivate/delete entries first or update in
  place where the web UI supports update.
- The inspected web UI utility code exposes import/delete for Actions and
  Outputs and update helpers for Inputs, Functions, and Widgets. If an
  installed Mycodo UI lacks an Action or Output update button, do not claim one;
  use the target installation's supported maintenance path and back up first.

## Testing And Verification Limits

This skill was produced from CPU/source inspection. Raspberry Pi
GPIO/I2C/UART/1-Wire/Bluetooth/camera access, systemd/nginx/InfluxDB service
mutation, Docker deployment, backup/restore, and full installer execution were
not run. Treat those surfaces as live-system risks requiring user confirmation
and target-host validation.

`testing=True` in module constructors is useful for dry instantiation because
base classes avoid some daemon/database measurement setup, and examples often
skip `try_initialize()` or driver access. It is not a complete simulator of the
web UI, database, InfluxDB, daemon, dependencies, or hardware.

## Stop Conditions

Stop and ask before:

- Installing `apt` or privileged system dependencies.
- Opening physical buses or camera devices on a production controller.
- Restarting the daemon, web frontend, systemd services, nginx, or InfluxDB.
- Changing Output states, PID tuning, Conditional/Trigger activation, or any
  device that can heat, cool, pump, dose, move, or energize equipment.
- Embedding real API keys, credentials, serial numbers, hostnames, or private
  installation paths in module files, logs, or prompts.
