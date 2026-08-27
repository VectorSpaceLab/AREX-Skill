# Mycodo Custom Module Contracts

This reference distills the runtime contracts for custom Inputs, Outputs,
Functions, Actions, and Widgets. Use it to review a module before upload or to
explain why a module imported but does not behave as expected.

## Universal Rules

- A custom module is a single Python file uploaded through the matching web UI
  page under `[Gear Icon] -> Configure -> Custom <kind>`.
- Mycodo loads the file as a Python module during import/update validation.
  Therefore top-level code must be limited to imports, constants, helper
  functions, information dictionaries, and class definitions.
- The information dictionary is the source of truth for UI name, unique id,
  measurement/channel metadata, dependencies, options, commands, and some hooks.
- The unique-name field is case-insensitive for collision checks and the imported
  filename is derived from the lower-case unique name on first import.
- Keep the unique-name field stable across updates. A changed upload filename is
  acceptable only when the dictionary unique key still matches the existing
  module unique key.
- Dependencies are declarative and must not be installed by top-level module
  code. Defer runtime imports to `initialize()` or another method so a missing
  driver produces a clear setup error rather than crashing import.

## Required Identity By Kind

| Kind | Information dictionary | Unique key | Display key | Expected class | Expected base | Required methods |
| --- | --- | --- | --- | --- | --- | --- |
| Input | `INPUT_INFORMATION` | `input_name_unique` | `input_name` | `InputModule` | `AbstractInput` | `initialize()`, `get_measurement()` |
| Output | `OUTPUT_INFORMATION` | `output_name_unique` | `output_name` | `OutputModule` | `AbstractOutput` | `initialize()`, `output_switch()`, `is_on()`, `is_setup()` |
| Function | `FUNCTION_INFORMATION` | `function_name_unique` | `function_name` | `CustomModule` | `AbstractFunction` | `initialize()`, usually `loop()`, optional `function_status()` |
| Action | `ACTION_INFORMATION` | `name_unique` | `name` | `ActionModule` | `AbstractFunctionAction` | `initialize()`, `run_action()`, `is_setup()` |
| Widget | `WIDGET_INFORMATION` | `widget_name_unique` | `widget_name` | `WidgetModule`, `CustomModule`, or no class when `no_class: True` | `AbstractWidget` for class-based Widgets | `execute_refresh()` for refreshable class Widgets |

The static validator checks class names conservatively. Mycodo import itself
primarily validates the information dictionary and dependency tuple shape; some
runtime method omissions only fail when the daemon or Dashboard tries to use the
module.

## Input Contract

`INPUT_INFORMATION` should usually include:

- `input_name_unique`: stable unique id for import, updates, and DB references.
- `input_manufacturer`, `input_name`, optional `input_name_short`, and optional
  `input_library` for UI display.
- `measurements_name` and `measurements_dict` unless the module uses a supported
  variable-measurement pattern.
- `measurements_use_same_timestamp`: `True` when all channel values in one
  acquisition should share one timestamp; `False` when values are timestamped as
  each `value_set()` occurs.
- `options_enabled` / `options_disabled`: built-in UI option names such as
  `period`, `pre_output`, `interface`, `measurements_select`, `i2c_location`,
  `uart_location`, `bt_location`, or `location`.
- Optional `interfaces`, bus/address defaults, `dependencies_module`,
  `custom_options`, `custom_channel_options`, and `custom_commands`.

Minimal multi-measurement shape:

```python
import copy
from mycodo.inputs.base_input import AbstractInput

measurements_dict = {
    0: {'measurement': 'temperature', 'unit': 'C'},
    1: {'measurement': 'humidity', 'unit': 'percent'},
}

INPUT_INFORMATION = {
    'input_name_unique': 'example_air_probe',
    'input_manufacturer': 'Example',
    'input_name': 'Example Air Probe',
    'measurements_name': 'Temperature/Humidity',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,
    'options_enabled': ['measurements_select', 'period'],
    'dependencies_module': [],
    'custom_options': [],
}

class InputModule(AbstractInput):
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)
        if not testing:
            self.setup_custom_options(INPUT_INFORMATION['custom_options'], input_dev)

    def initialize(self):
        pass

    def get_measurement(self):
        self.return_dict = copy.deepcopy(measurements_dict)
        if self.is_enabled(0):
            self.value_set(0, 22.5)
        if self.is_enabled(1):
            self.value_set(1, 55.0)
        return self.return_dict
```

Important Input details:

- `measurements_dict` keys are channel numbers. `value_set(channel, value)` must
  use a channel key that exists and is enabled.
- `value_set()` converts values to float and rejects `None`; catch driver errors
  and log useful messages rather than returning stale data.
- If `is_enabled(channel)` is checked, disabled measurement channels are skipped.
- Input `custom_commands` are UI controls. A button entry with id `calibrate`
  expects an `InputModule.calibrate(self, args_dict)` method.

## Output Contract

`OUTPUT_INFORMATION` should usually include:

- `output_name_unique`, `output_name`, optional `output_library`.
- `measurements_dict` for values the Output records, such as duration seconds.
- `channels_dict` mapping output channels to output `types` and measurement
  channel ids.
- `output_types`: one or more of `on_off`, `pwm`, `volume`, or value-like types
  supported by the installed Mycodo version.
- `options_enabled` / `options_disabled`, `interfaces`, `dependencies_module`,
  `custom_options`, `custom_channel_options`, and optional `custom_commands`.

Minimal single-channel On/Off Output shape:

```python
from mycodo.outputs.base_output import AbstractOutput

measurements_dict = {0: {'measurement': 'duration_time', 'unit': 's'}}
channels_dict = {0: {'types': ['on_off'], 'measurements': [0]}}

OUTPUT_INFORMATION = {
    'output_name_unique': 'example_safe_relay',
    'output_name': 'Example Safe Relay',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['on_off'],
    'options_enabled': ['button_on', 'button_send_duration'],
    'dependencies_module': [],
    'custom_options': [],
    'custom_channel_options': [],
}

class OutputModule(AbstractOutput):
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)
        self.output_setup = False

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)
        self.output_setup = True

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None, output_channel=None):
        self.output_states[output_channel] = (state == 'on')
        return 'ok'

    def is_on(self, output_channel=None):
        return self.output_states.get(output_channel) if output_channel is not None else self.output_states

    def is_setup(self):
        return self.output_setup
```

Important Output details:

- Call `setup_output_variables(OUTPUT_INFORMATION)` during `initialize()` to
  seed state dictionaries for every output channel.
- `output_switch()` receives normalized calls from Mycodo's output machinery;
  it must handle state, channel, and relevant amount/duty/volume parameters.
- `is_on()` should return channel-specific state when a channel is supplied.
- `custom_channel_options` are read per `OutputChannel`; use
  `setup_custom_channel_options_json()` to get a nested dictionary keyed by
  option id and channel.

## Function Contract

`FUNCTION_INFORMATION` should usually include:

- `function_name_unique` and `function_name`.
- Optional `measurements_dict` and `channels_dict` if the Function stores values.
- `measurements_variable_amount` and `channel_quantity_same_as_measurements`
  when the user chooses variable measurements/channels.
- `options_enabled`, commonly `custom_options`, `function_status`,
  `measurements_select`, or `measurements_configure`.
- `custom_options` for inactive-only settings and optional
  `custom_channel_options` for per-channel settings.

Periodic Function pattern:

```python
import time
from mycodo.databases.models import CustomController
from mycodo.functions.base_function import AbstractFunction
from mycodo.utils.database import db_retrieve_table_daemon

FUNCTION_INFORMATION = {
    'function_name_unique': 'example_periodic_status',
    'function_name': 'Example Periodic Status',
    'options_enabled': ['custom_options', 'function_status'],
    'dependencies_module': [],
    'custom_options': [
        {'id': 'period', 'type': 'float', 'default_value': 60.0,
         'required': True, 'name': 'Period (Seconds)',
         'phrase': 'Time between loop executions'},
    ],
}

class CustomModule(AbstractFunction):
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)
        self.period = None
        self.timer_loop = time.time()
        custom_function = db_retrieve_table_daemon(CustomController, unique_id=self.unique_id)
        self.setup_custom_options(FUNCTION_INFORMATION['custom_options'], custom_function)
        if not testing:
            self.try_initialize()

    def initialize(self):
        self.timer_loop = time.time() + self.period

    def loop(self):
        if self.timer_loop > time.time():
            return
        while self.timer_loop < time.time():
            self.timer_loop += self.period
        self.logger.info('Function tick')

    def function_status(self):
        return {'string_status': 'ok', 'error': []}
```

Important Function details:

- Function settings in `custom_options` are intended to be changed while the
  Function is inactive.
- `function_status()` returns a dictionary; the Function Status Widget displays
  status content on Dashboards.
- Functions that write measurements to InfluxDB should populate channel data
  with valid measurement/unit IDs and conversions before calling the write
  helper used by the installed Mycodo version.
- Updating an active Function can restart the daemon; plan maintenance windows.

## Action Contract

`ACTION_INFORMATION` should usually include:

- `name_unique`, `name`, optional `library`, `manufacturer`.
- `application`: usually `['inputs']`, `['functions']`, or both, depending on
  where the Action may be attached.
- `message` and `usage` for UI guidance.
- `dependencies_module` and `custom_options`.

Action pattern:

```python
from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'example_append_message',
    'name': 'Example Append Message',
    'manufacturer': 'Example',
    'application': ['functions', 'inputs'],
    'message': 'Appends a message when executed.',
    'usage': 'Use self.run_action("ACTION_ID") from Conditional or Function code.',
    'dependencies_module': [],
    'custom_options': [
        {'id': 'suffix', 'type': 'text', 'default_value': 'done',
         'name': 'Suffix', 'phrase': 'Text appended to the message'},
    ],
}

class ActionModule(AbstractFunctionAction):
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)
        self.suffix = None
        action = db_retrieve_table_daemon(Actions, unique_id=self.unique_id)
        self.setup_custom_options(ACTION_INFORMATION['custom_options'], action)
        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        dict_vars.setdefault('message', '')
        dict_vars['message'] += ' ' + str(self.suffix)
        return dict_vars

    def is_setup(self):
        return self.action_setup
```

Important Action details:

- `dict_vars` commonly contains `message` and may contain `value`; validate keys
  defensively and return the dictionary.
- Options of type `select_measurement`, `select_measurement_from_this_input`,
  `select_measurement_channel`, and `select_device` create suffixed attributes
  such as `_device_id`, `_measurement_id`, `_channel_id`, or `_id`.
- Action deletion is blocked while Action entries still use the module.

## Widget Contract

`WIDGET_INFORMATION` should usually include:

- `widget_name_unique`, `widget_name`, optional `widget_library`.
- `widget_width` and `widget_height` for default Dashboard layout.
- `dependencies_module` and `custom_options`.
- Dashboard template snippets: `widget_dashboard_head`,
  `widget_dashboard_title_bar`, `widget_dashboard_body`, `widget_dashboard_js`,
  `widget_dashboard_js_ready`, and `widget_dashboard_js_ready_end`.
- Optional `endpoints` as tuples `(route, endpoint_name, view_function, methods)`
  for Widgets that expose Flask routes. Endpoint functions must enforce
  authentication and permissions before returning sensitive data.
- Optional lifecycle hooks such as creation/modification/deletion helpers when
  the installed Mycodo version supports them.

Simple no-class Widget pattern:

```python
WIDGET_INFORMATION = {
    'widget_name_unique': 'example_text_widget',
    'widget_name': 'Example Text Widget',
    'widget_library': '',
    'no_class': True,
    'dependencies_module': [],
    'widget_width': 6,
    'widget_height': 4,
    'custom_options': [
        {'id': 'body_text', 'type': 'text', 'default_value': 'Hello',
         'name': 'Body Text', 'phrase': 'Text to render'},
    ],
    'widget_dashboard_head': '<!-- no head content -->',
    'widget_dashboard_title_bar': '<span>{{each_widget.name}}</span>',
    'widget_dashboard_body': '<span>{{widget_options["body_text"]}}</span>',
    'widget_dashboard_js': '<!-- no js -->',
    'widget_dashboard_js_ready': '<!-- no ready js -->',
    'widget_dashboard_js_ready_end': '<!-- no end js -->',
}
```

Important Widget details:

- Dashboard snippets are rendered into the Dashboard page in specific locations;
  JavaScript that needs element IDs should include `each_widget.unique_id` to
  avoid collisions between multiple instances.
- Use the `|safe` template filter only for content that is intentionally HTML and
  not user-supplied or untrusted.
- Updating a Widget regenerates Widget HTML and reloads the frontend. If any
  Dashboard Widget entry uses the module, the daemon is restarted.

## Custom Options And Commands

Supported option types observed in the base controller include:

- Primitive/user-entry: `integer`, `float`, `bool`, `text`, `multiline_text`.
- Selection: `select`, `select_custom_choices`, `select_multi_measurement`.
- Measurement/channel selectors: `select_measurement`,
  `select_measurement_from_this_input`, `select_channel`,
  `select_measurement_channel`, `select_type_measurement`, `select_type_unit`.
- Device selector: `select_device`.
- Layout/information: `message`, `new_line`.

Option dictionary rules:

- Every rendered option except `new_line` needs `default_value`.
- Every option except `message` and `new_line` needs a stable `id`.
- `required: True` logs if the user value is missing; it does not remove the
  need for defensive runtime defaults.
- `constraints_pass` is a callable that returns a tuple shaped like
  `(all_passed, errors, controller_object)`. Use it to reject invalid UI values,
  not to perform driver I/O or system changes.
- `select` and `select_custom_choices` may use `options_select` with pairs such
  as `('A', 'Display A')`.

`custom_commands` are buttons and inputs rendered in the UI. A command button
with id `button_one` calls a module method named `button_one(self, args_dict)`;
input command values are passed in `args_dict` keyed by their command ids.

## Dependencies

`dependencies_module` must be a list of 3-item tuples when present:

```python
'dependencies_module': [
    ('pip-pypi', 'example-driver', 'example-driver==1.2.3'),
    ('apt', 'example-system-package', 'example-system-package'),
    ('internal', 'file-exists /opt/Mycodo/example_marker', 'example-marker'),
]
```

Rules:

- First tuple item must be `pip-pypi`, `apt`, or `internal`.
- Tuple items must be non-empty.
- `apt` and privileged dependency installs can mutate the host; ask before
  performing them.
- Declare the narrowest dependency required for the selected module. Do not add
  broad development extras, hardware stacks, or unrelated drivers.
- Defer importing declared packages until `initialize()` or later to keep module
  import validation clear and recoverable.

## Update, Delete, And Restart Semantics

- New imports validate the uploaded file, derive the destination filename from
  the lower-case unique key, move the temp file into the custom kind directory,
  and reload the frontend.
- Input, Function, and Widget updates load both uploaded and existing modules,
  require the same unique key, preserve side-loaded existing filenames when the
  parser records them, overwrite the existing file, and reload the frontend.
- Updating an active Input or active Function restarts the daemon.
- Updating a Widget regenerates Widget HTML; if a Dashboard contains a Widget of
  that graph type, the daemon restarts.
- Delete is blocked while database entries still use the module. For Widgets,
  delete Dashboard entries first; for Outputs, delete Output entries first; for
  Actions, delete Action entries first; for Inputs/Functions, deactivate/delete
  affected controller entries first.
