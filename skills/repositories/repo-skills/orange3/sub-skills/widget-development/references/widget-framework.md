# Widget Framework Reference

This reference covers the Orange widget framework surfaces that future agents most often need when building or repairing widgets. It intentionally avoids domain-specific data/model/visualization algorithms except where a framework pattern needs a concrete value.

## Minimal widget anatomy

A normal Orange widget is a subclass of `Orange.widgets.widget.OWWidget`.

```python
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg

class OWExample(OWWidget):
    name = "Example"
    description = "Minimal framework example"
    icon = "icons/Example.svg"      # package resource if distributed in a widget package
    priority = 10
    keywords = "example, widget"
    want_main_area = False

    class Inputs:
        value = Input("Value", object, default=True)

    class Outputs:
        result = Output("Result", object)

    class Error(OWWidget.Error):
        invalid_value = Msg("Invalid input: {}")

    auto_apply = Setting(True)

    def __init__(self):
        super().__init__()
        self.value = None
        gui.label(self.controlArea, self, "Current value: %(value)s")
        self.apply_button = gui.auto_apply(
            self.buttonsArea, self, "auto_apply", "Apply", commit=self.commit
        )

    @Inputs.value
    def set_value(self, value):
        self.value = value

    def handleNewSignals(self):
        self.commit()

    def commit(self):
        self.Error.invalid_value.clear()
        self.Outputs.result.send(self.value)
```

Important lifecycle points:

- `__init__` builds Qt controls and initializes non-setting runtime state. `Setting` and `ContextSetting` values are already restored before `__init__` runs.
- Input handlers decorated with `@Inputs.<signal>` should usually set internal state only. Put coalesced recomputation in `handleNewSignals()` when multiple inputs may arrive together.
- Send outputs with `self.Outputs.<signal>.send(value)`. Send `None` when an output should be cleared.
- Use `onDeleteWidget()` for cleanup such as cancelling workers, shutting down executors, closing files, and releasing non-Qt resources.
- Implement `send_report()` when the widget should contribute a report. Use the generic report helpers listed below.

## Metadata and discovery

Canvas discovery expects a concrete final widget class with at least a non-empty `name`. Usual class attributes are:

| Attribute | Purpose | Notes |
| --- | --- | --- |
| `name` | Canvas-visible widget title | Required for final widgets and tested by Orange's widget test helpers. |
| `description` | Short catalog/help description | Keep concise and user-facing. |
| `icon` | Relative icon resource | Optional for experiments, expected for packaged widgets. |
| `priority` | Category order | Smaller values appear earlier. |
| `keywords` | Search terms | Use a comma-separated string; Orange tests reject list syntax for opted-in modules. |
| `category` | Widget category override | Usually supplied by package discovery/category metadata instead. |
| `want_main_area` | Whether a central main area is created | Set `False` for control-only widgets. |
| `resizing_enabled` | Whether the widget is resizable | Useful for compact base widgets. |

Use new-style signal declarations whenever possible; old-style `inputs`/`outputs` tuple lists exist for backward compatibility but are deprecated for new code.

## Inputs, outputs, and multi-inputs

Verified signatures:

```python
Input(name, type, id=None, doc=None, replaces=None, *,
      multiple=False, default=False, explicit=False,
      auto_summary=None, closing_sentinel=None)
Output(name, type, id=None, doc=None, replaces=None, *,
       default=False, explicit=False, dynamic=True, auto_summary=None)
MultiInput(*args, filter_none=False, **kwargs)
```

Patterns:

- Use `default=True` when several signals of the same type exist and Canvas should auto-select one.
- Use `explicit=True` for supplementary outputs/inputs that should not be auto-connected unless chosen by the user.
- Use `multiple=True` only when handler order is unimportant and the handler accepts `(value, id)`.
- Prefer `MultiInput` for ordered multi-inputs. It registers separate set/insert/remove handlers:

```python
from orangewidget.utils.signals import MultiInput

class Inputs:
    values = MultiInput("Values", object, filter_none=True)

@Inputs.values
def set_value(self, index: int, value: object):
    self.values[index] = value

@Inputs.values.insert
def insert_value(self, index: int, value: object):
    self.values.insert(index, value)

@Inputs.values.remove
def remove_value(self, index: int):
    del self.values[index]
```

## Messages and I/O summaries

Use nested message classes for independent warning/error/info states:

```python
class Warning(OWWidget.Warning):
    ignored_input = Msg("Ignoring unsupported input")

self.Warning.ignored_input()
self.Warning.ignored_input.clear()
self.Warning.clear()
self.clear_messages()
```

For status-bar summaries, call `self.info.set_input_summary(...)` and `self.info.set_output_summary(...)`. Initialize summaries in `__init__` when the empty state matters. Output and input signals can also request or suppress automatic summaries with `auto_summary`.

## Settings and context settings

Verified signatures:

```python
Setting(default, *args, **kwargs)
ContextSetting(default, *, required=2, exclude_attributes=False, exclude_metas=False, **data)
DomainContextHandler(*, match_values=0, first_match=True, **kwargs)
```

Use ordinary settings for GUI state that is independent of input data:

```python
class OWExample(OWWidget):
    threshold = Setting(0.5)
    auto_apply = Setting(True)
```

Use context settings when stored values depend on the incoming domain/schema:

```python
from Orange.widgets.settings import ContextSetting, DomainContextHandler

class OWContextExample(OWWidget):
    settingsHandler = DomainContextHandler()
    selected_variable = ContextSetting(None)

    @Inputs.data
    def set_data(self, data):
        self.closeContext()
        self.data = data
        self.selected_variable = None
        if data is not None:
            self.openContext(data.domain)
        self.commit()
```

Context order matters:

1. Clean runtime state without destroying values that need to be saved.
2. `closeContext()` before replacing domain-dependent state.
3. Set sensible defaults for a fresh context.
4. `openContext(domain_or_data.domain)`.
5. Update controls, plots, outputs, and messages.

When changing stored setting formats, bump `settings_version` and implement:

```python
def migrate_settings(settings, version):
    ...

def migrate_context(context, version):
    ...
```

Helpers include `rename_setting(settings, old_name, new_name)` and `migrate_str_to_variable(settings, names=None, none_placeholder=None)`. If a saved context is no longer valid, `migrate_context` may raise `IncompatibleContext` so Orange drops that context instead of crashing.

## Concurrency and cancellation

For new threaded widgets prefer `Orange.widgets.utils.concurrent.ConcurrentWidgetMixin` over the older manual `ThreadExecutor`/`FutureWatcher` pattern.

Verified APIs:

```python
ConcurrentWidgetMixin.start(self, task: Callable, *args, **kwargs)
ConcurrentWidgetMixin.cancel(self)
ConcurrentWidgetMixin.shutdown(self)
TaskState.set_status(self, text: str)
TaskState.set_progress_value(self, value: float)
TaskState.set_partial_result(self, value)
TaskState.is_interruption_requested(self) -> bool
```

Pattern:

```python
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin, TaskState


def run_heavy(payload, state: TaskState):
    for i, chunk in enumerate(payload):
        if state.is_interruption_requested():
            return None
        state.set_status("Working...")
        state.set_progress_value(100 * (i + 1) / len(payload))
        state.set_partial_result(chunk)
    return payload

class OWHeavy(OWWidget, ConcurrentWidgetMixin):
    def __init__(self):
        OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)

    def start_work(self):
        self.start(run_heavy, self.payload)

    def on_partial_result(self, result):
        ...

    def on_done(self, result):
        self.Outputs.result.send(result)

    def on_exception(self, ex: Exception):
        self.Error.failed(str(ex))

    def onDeleteWidget(self):
        self.shutdown()
        super().onDeleteWidget()
```

Do not start a new task from `on_done` or `on_exception`; the mixin asserts this to prevent reentrancy. On new input, call `cancel()` or let `start()` cancel the previous task before scheduling the next one.

## Framework base helpers

- `OWBaseLearner` in `Orange.widgets.utils.owlearnerwidget` is a model-widget base. A concrete subclass must set `name` and `LEARNER`; its metaclass gives each subclass its own typed `learner` and `model` outputs. Use it only when the task is specifically a learner widget; keep learner semantics in the supervised-modeling sub-skill.
- `OWBaseSql` in `Orange.widgets.utils.owbasesql` is a credential-backed database widget base. Subclasses override `get_backend()` and `get_table()`. It stores host/port/database/schema as settings, obtains username/password through `CredentialManager`, shows `Error.connection`, and sends `Outputs.data`. Treat it as optional service-bound support.
- `check_sql_input` and `check_sql_input_sequence` convert small `SqlTable` inputs to in-memory `Table` and show a `download_sql_data` error for large SQL inputs. Use them on input handlers that expect in-memory tables.

## Reporting hooks

`OWWidget` mixes in Orange's `DataReport` helpers. Useful generic methods:

```python
self.report_items("Options", [("Threshold", self.threshold)])
self.report_data("Data", self.data)
self.report_domain("Domain", self.data.domain)
self.report_data_brief("Data", self.data)
self.report_plot()
self.report_caption("Shown when enough input is available.")
```

`describe_data(data)`, `describe_domain(domain)`, `describe_data_brief(data)`, and `describe_domain_brief(domain)` return ordered dictionaries suitable for reports. Keep report text deterministic and avoid storing secrets such as SQL passwords.
