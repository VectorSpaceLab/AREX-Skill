# Custom Module Recipes

Use these recipes when building or revising Mycodo custom modules. They are for
fast authoring plus review; live import messages from the target Mycodo instance
are still authoritative.

## Recipe 1: New Input

1. Pick a stable unique id such as `vendor_sensor_model`.
2. Decide measurement channels first, e.g. channel `0` temperature in `C` and
   channel `1` humidity in `percent`.
3. Add `measurements_name`, `measurements_dict`, and
   `measurements_use_same_timestamp` to `INPUT_INFORMATION`.
4. Add built-in UI fields to `options_enabled`; `['measurements_select',
   'period']` is a common interval-sensor start.
5. Add `dependencies_module: []` unless a driver is truly required.
6. Implement `InputModule(AbstractInput)`: constructor calls `super(...)`,
   `initialize()` imports drivers/opens clients, and `get_measurement()`
   deep-copies `measurements_dict`, fills enabled channels with `value_set()`,
   and returns `self.return_dict`.
7. Validate before upload:

```bash
python scripts/validate_custom_module.py --kind input my_input.py
```

Common Input pitfalls: stale `return_dict`, display names instead of
measurement/unit IDs, `value_set()` channel not present in `measurements_dict`,
and top-level hardware imports that fail before Mycodo can show dependency
messages.

## Recipe 2: Output With Channels

1. Pick `output_name_unique` and `output_name`.
2. Define `measurements_dict` for values the Output records. Duration Outputs
   commonly use `{'measurement': 'duration_time', 'unit': 's'}`.
3. Define `channels_dict`; each output channel lists supported output `types`
   and measurement channel ids:

```python
measurements_dict = {0: {'measurement': 'duration_time', 'unit': 's'}}
channels_dict = {0: {'types': ['on_off'], 'measurements': [0]}}
```

4. Set `output_types` consistently, such as `['on_off']` or `['pwm']`.
5. Implement `OutputModule(AbstractOutput)` and call
   `self.setup_output_variables(OUTPUT_INFORMATION)` in `initialize()`.
6. Ensure `output_switch()` never energizes hardware before the user has saved
   the intended channel/pin/interface options.
7. Use `custom_channel_options` for per-channel labels, calibration, or dynamic
   choices; load with `setup_custom_channel_options_json()`.
8. Validate:

```bash
python scripts/validate_custom_module.py --kind output my_output.py
```

Output update note: the inspected web UI utility has import/delete flows for
Outputs. If the target UI does not provide an update action, do not delete a
module that still has Output entries; deletion is blocked, and out-of-band file
replacement is maintenance requiring backup and explicit user approval.

## Recipe 3: Periodic Function

1. Choose `function_name_unique` and `function_name`.
2. Enable `custom_options` for settings and `function_status` if the UI or a
   Dashboard Widget should show status.
3. Include a period custom option and a start offset if first-run timing matters.
4. Implement `CustomModule(AbstractFunction)`: constructor sets defaults, loads
   saved options with `setup_custom_options()`, calls `try_initialize()` only
   when not testing, `initialize()` sets timers/clients, `loop()` returns until
   its period elapses, and `function_status()` returns
   `{'string_status': text, 'error': []}` when status is enabled.
5. Validate:

```bash
python scripts/validate_custom_module.py --kind function my_function.py
```

Function update consequence: if at least one controller using the module is
active, updating reloads the frontend and restarts the daemon. Warn users before
updating a Function that controls Outputs, PID, Conditional, Trigger, or an
environmental process.

## Recipe 4: Variable-Measurement Function

Use this when the user chooses how many channels/measurements the Function emits.

```python
measurements_dict = {0: {'name': 'value'}}
channels_dict = {0: {}}
FUNCTION_INFORMATION = {
    'function_name_unique': 'example_variable_channels',
    'function_name': 'Example Variable Channels',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'measurements_variable_amount': True,
    'channel_quantity_same_as_measurements': True,
    'options_enabled': ['measurements_select', 'custom_options'],
    'custom_options': [],
    'custom_channel_options': [],
}
```

In `loop()`, iterate over `self.channels_measurement` rather than hard-coding
channel count. Preserve each selected measurement's measurement id and unit
unless a valid conversion changes them. Load per-channel options from saved
FunctionChannel rows with `setup_custom_channel_options_json()`.

## Recipe 5: Action

1. Choose `name_unique` and `name`.
2. Set `application` to the controller families that may use the Action, such as
   `['inputs']`, `['functions']`, or both.
3. Use `message` for UI description and `usage` for a callable example.
4. Add `custom_options` for target controller IDs, measurements, channels, text,
   thresholds, or numeric parameters.
5. Implement `ActionModule(AbstractFunctionAction)` and return `dict_vars` from
   `run_action()`.
6. Validate:

```bash
python scripts/validate_custom_module.py --kind action my_action.py
```

Action selector attribute names: `select_measurement` creates `<id>_device_id`
and `<id>_measurement_id`; `select_measurement_channel` creates those plus
`<id>_channel_id`; `select_device` creates `<id>_id`.

## Recipe 6: Simple Dashboard Widget

1. Choose `widget_name_unique` and `widget_name`.
2. Use `no_class: True` if the Widget only renders Dashboard snippets and does
   not need a backend loop or refresh method.
3. Define `widget_width`, `widget_height`, `dependencies_module`, and
   `custom_options`.
4. Provide all Dashboard snippets: `widget_dashboard_head`,
   `widget_dashboard_title_bar`, `widget_dashboard_body`, `widget_dashboard_js`,
   `widget_dashboard_js_ready`, and `widget_dashboard_js_ready_end`.
5. When creating element IDs or JavaScript function names, include
   `{{each_widget.unique_id}}` to avoid collisions across several Dashboard
   instances.
6. Validate:

```bash
python scripts/validate_custom_module.py --kind widget my_widget.py
```

Do not render untrusted user text with `|safe` unless the Widget intentionally
accepts HTML and the deployment accepts that risk. Widget endpoints must check
authentication and permission before returning information or mutating state.

## Recipe 7: Class-Based Widget

Use this when the Widget needs backend work beyond static Dashboard snippets.

1. Keep `WIDGET_INFORMATION` complete as in the simple Widget recipe.
2. Implement a class such as `WidgetModule(AbstractWidget, threading.Thread)`.
3. In the constructor, initialize threading if used, call `super().__init__(...)`,
   then load custom options with `setup_custom_options_json()`.
4. Use initialization methods to load files, clients, and state. Do not do
   blocking work at import time.
5. Implement `execute_refresh()` if the Dashboard should fetch fresh data.
6. Honor a `running` flag and period timing for background loops.

Widget update consequence: update regenerates Widget HTML, reloads the frontend,
and restarts the daemon if any Dashboard Widget entry uses the module.

## Recipe 8: Custom Options And Constraints

A robust option entry includes stable id, supported type, default, and UI text:

```python
{
    'id': 'sample_period',
    'type': 'float',
    'default_value': 10.0,
    'required': True,
    'constraints_pass': constraints_pass_positive_value,
    'name': 'Sample Period (Seconds)',
    'phrase': 'Seconds between samples'
}
```

Guidelines:

- Never reuse an `id` for a different meaning after users have saved settings.
- Use `new_line` for UI layout and `message` for standalone UI text.
- `constraints_pass` must validate a proposed value and return
  `(bool, list_of_errors, controller_object)`.
- Avoid network calls, package installs, file writes, bus access, and service
  changes inside constraints.

## Recipe 9: Dependencies

Use dependency tuples only for real dependencies:

```python
'dependencies_module': [
    ('pip-pypi', 'sensor-driver', 'sensor-driver==2.0.0'),
]
```

Review whether the dependency is optional, whether it can install without
hardware attached, whether it requires `apt`, kernel modules, udev, permissions,
or service restarts, and whether imports are deferred to `initialize()`.

## Recipe 10: Update Existing Module

1. Identify the module by its information dictionary unique key, not upload
   filename.
2. Keep the unique key identical to the existing module.
3. Warn users that active Inputs and active Functions trigger daemon restart on
   supported update paths; Widgets used on Dashboards also trigger daemon
   restart after HTML regeneration.
4. Run the validator before upload.
5. Upload through the update UI when available.
6. After update, verify frontend reload and daemon log setup messages.
7. If side-loaded filename differs from the unique key, supported Input,
   Function, and Widget update paths preserve the existing file path when
   Mycodo's parser records it.

Do not delete/reimport just to update while live entries exist; Mycodo blocks
delete for in-use modules and deletion can remove user configuration.

## Pre-upload Review Checklist

- [ ] Required information dictionary exists and has stable unique/name keys.
- [ ] Expected class name and base class are present unless Widget `no_class` is
      deliberately true.
- [ ] No unsafe top-level execution: subprocess, network, file writes, sleeps,
      daemon calls, or hardware opens.
- [ ] `dependencies_module` is an explicit list of valid 3-tuples or `[]`.
- [ ] `custom_options`, `custom_channel_options`, and `custom_commands` are
      lists when present.
- [ ] Button command ids have matching methods.
- [ ] Selector option ids have the suffixed attributes expected by Mycodo.
- [ ] Measurements and units exist or are planned for creation before import.
- [ ] Channels only refer to declared measurement channels.
- [ ] `testing=True` dry paths do not hit live hardware or mandatory DB state.
- [ ] Hardware/service/system mutations are explicitly approved by the user.
