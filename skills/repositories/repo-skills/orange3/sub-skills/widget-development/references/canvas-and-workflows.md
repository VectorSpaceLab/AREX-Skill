# Canvas, Preview, Tests, Workflows, and Catalogs

Use this reference for runtime checks around Orange Canvas, widget discovery, `WidgetPreview`, widget unit tests, `.ows` workflow loading, and widget-catalog generation.

## Launching Canvas and headless checks

- `python -m Orange.canvas` starts the Orange GUI from an installed package.
- The `orange-canvas` entry point exposes Canvas CLI help and maintenance options such as clearing widget settings.
- For headless Linux/CI/container runs, set `QT_QPA_PLATFORM=offscreen` before creating a `QApplication`, running previews/tests, loading workflows, or rendering widget catalog icons.
- Do not run interactive GUI loops during automated verification unless the task explicitly asks for manual inspection. Prefer `WidgetPreview(...).run(no_exec=True, no_exit=True)` or `WidgetTest` assertions.

## Widget discovery and registry

Orange Canvas discovers widgets through entry points in the `orange.widgets` group. Verified registry pattern:

```python
from Orange.canvas.config import Config
from orangecanvas.registry import WidgetRegistry

registry = WidgetRegistry()
discovery = Config.widget_discovery(registry)
discovery.run(Config.widgets_entry_points())

# Orange's catalog script normalizes category.widgets from the registry internals.
for category, widgets in registry._categories_dict.values():
    category.widgets = widgets
```

The inspected package produced seven core categories: `Data`, `Transform`, `Visualize`, `Model`, `Evaluate`, `Unsupervised`, and `Orange Obsolete`, with 105 discoverable widgets after category normalization. If discovery returns categories but no widgets, check whether `category.widgets` was normalized as above before assuming discovery failed.

Discovery-sensitive class facts:

- Final widget classes need a `name`.
- Use new-style `class Inputs` / `class Outputs` with `Input` and `Output` descriptors for new code.
- `keywords` should be a comma-separated string for Orange's keyword checks, not a list.
- Add-on widgets must be importable from their package entry point; import-time optional dependency failures can hide the widget.

## `WidgetPreview` for development

Verified signature:

```python
WidgetPreview(widget_cls).run(input_data=None, *, no_exec=False, no_exit=False, **kwargs)
```

Common preview fence:

```python
if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(OWExample).run(no_exit=False)
```

Input examples:

```python
# Default/single input signal selected by object type.
WidgetPreview(OWExample).run(some_value)

# Explicit handler names for multiple signals.
WidgetPreview(OWExample).run(set_data=data, set_subset_data=subset)

# Multi-input handler receives tuple chunks.
WidgetPreview(OWMulti).run([(value1, "first"), (value2, "second")])

# Non-interactive smoke/debug pass.
previewer = WidgetPreview(OWExample)
previewer.run(data, no_exec=True, no_exit=True)
previewer.send_signals(set_extra=extra)
previewer.tear_down()
```

Important preview behavior:

- Without `no_exit=True`, `run()` tears down the widget and calls `sys.exit(exit_code)`.
- `no_exec=True` skips showing the widget and does not enter the event loop.
- Preview sends signals and then calls `handleNewSignals()`.
- If there are multiple matching input signals and none is uniquely default, positional `input_data` raises a `ValueError`; use keyword handler names.

## Widget unit tests

Use `Orange.widgets.tests.base.WidgetTest` for assertion-backed widget tests. Verified helpers:

```python
create_widget(cls, stored_settings=None, reset_default_settings=True, **kwargs)
send_signal(input, value=..., *args, widget=None, wait=-1)
send_signals(signals, *args, widget=None, wait=-1)
get_output(output=None, widget=None, wait=5000)
wait_until_finished(widget=None, timeout=5000)
wait_until_stop_blocking(widget=None, wait=5000)
process_events(until=None, timeout=5000)
```

Test skeleton:

```python
from Orange.widgets.tests.base import WidgetTest

class TestOWExample(WidgetTest):
    def setUp(self):
        self.widget = self.create_widget(OWExample)

    def test_signal_roundtrip(self):
        self.send_signal(self.widget.Inputs.value, object())
        self.wait_until_finished()
        self.assertIsNotNone(self.get_output(self.widget.Outputs.result))

    def test_stored_settings(self):
        self.widget.mode = 1
        settings = self.widget.settingsHandler.pack_data(self.widget)
        restored = self.create_widget(OWExample, stored_settings=settings)
        self.assertEqual(restored.mode, 1)
```

`GuiTest` ensures a `QApplication` exists. `WidgetTest` creates widgets with a dummy signal manager, resets settings by default, processes pending events after construction, tears down widgets safely, and lets tests inspect warning/error messages and outputs.

## Workflow loading

The workflow compatibility test pattern uses `orangewidget.workflow.widgetsscheme.WidgetsScheme` and a populated registry:

```python
from AnyQt.QtTest import QTest
from Orange.canvas.config import Config
from orangecanvas.registry import WidgetRegistry
from orangewidget.workflow import widgetsscheme

reg = WidgetRegistry()
discovery = Config.widget_discovery(reg)
discovery.run(Config.widgets_entry_points())

scheme = widgetsscheme.WidgetsScheme()
scheme.widget_manager.set_creation_policy(scheme.widget_manager.Immediate)
scheme.signal_manager.pause()
try:
    with open("workflow.ows", "rb") as f:
        scheme.load_from(f, registry=reg)
finally:
    scheme.clear()
    scheme.deleteLater()
    QTest.qWait(0)
```

Key rules:

- `WidgetsScheme.load_from(stream, registry=reg)` requires an empty scheme and accepts a path string or binary stream.
- Pause signal propagation while loading compatibility fixtures; resume only when the workflow should execute.
- Use `Immediate` creation policy when the load should instantiate all widgets.
- Always clear and delete the scheme to avoid lingering Qt objects.
- For user workflows, the guidance above is sufficient for loading arbitrary `.ows` files; keep any package test-fixture checks outside runtime instructions.

For non-interactive execution of an `.ows` file, Orange provides a Canvas runner that constructs a registry, loads the workflow, creates every widget, resumes signal propagation, and exits with a non-zero status if node error messages remain. Use this only for short, deterministic workflows.

## Widget catalog tooling

The bundled script creates a self-contained widget catalog from the installed Orange package and discovered entry points:

```bash
QT_QPA_PLATFORM=offscreen python scripts/create_widget_catalog.py \
  --output ./orange-widget-catalog \
  --no-icons --no-help
```

Useful modes:

- `--list-categories` prints discovered categories.
- `--categories Data,Transform` filters output.
- `--no-icons` avoids Qt graphics rendering.
- `--no-help` avoids WebEngine/help URL initialization.
- With icons enabled, PNGs are written under `<output>/icons/` and referenced from `widgets.json`.

The script intentionally uses the installed package's registry rather than repository files. If add-on widgets must appear, install the add-on into the same environment before running discovery.
