---
name: widget-development
description: "Build, preview, test, and load Orange widgets and Canvas workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Orange3 Widget Development

Use this sub-skill when the task is about Orange's widget framework rather than a specific data-mining method: authoring an `OWWidget`, wiring GUI controls and settings, previewing or unit-testing widgets, loading `.ows` Canvas workflows, debugging widget discovery, or generating a widget catalog from the installed Orange package.

## Route by task

- **New or revised widget class** → read [`references/widget-framework.md`](references/widget-framework.md), then [`references/gui-controls.md`](references/gui-controls.md). Use `OWWidget`, new-style `Inputs`/`Outputs`, `Setting`/`ContextSetting`, `Msg` message classes, and a `WidgetPreview` fence.
- **GUI control binding or settings** → read [`references/gui-controls.md`](references/gui-controls.md), then the context/settings section in [`references/widget-framework.md`](references/widget-framework.md).
- **Preview, tests, or headless Qt** → read [`references/canvas-and-workflows.md`](references/canvas-and-workflows.md) and [`references/troubleshooting.md`](references/troubleshooting.md). Prefer `WidgetPreview` for interactive/manual checks and `Orange.widgets.tests.base.WidgetTest` for assertions.
- **Canvas workflow loading or compatibility** → read [`references/canvas-and-workflows.md`](references/canvas-and-workflows.md). Use `WidgetsScheme.load_from(..., registry=reg)` or the non-interactive Canvas runner; pause signal propagation while loading test workflows.
- **Widget discovery/catalog work** → read [`references/canvas-and-workflows.md`](references/canvas-and-workflows.md), then run the bundled [`scripts/create_widget_catalog.py`](scripts/create_widget_catalog.py) against an installed Orange package.
- **Failure triage** → read [`references/troubleshooting.md`](references/troubleshooting.md) first; it covers discovery, missing metadata/I/O, stored settings, context migrations, GUI binding, Qt platform/offscreen issues, preview exits, background cancellation, SQL credential errors, and workflow-loading failures.

## Operating rules

1. Keep widget-development guidance framework-focused. Do not explain package-specific data, model, projection, visualization, or evaluation semantics except when they demonstrate the widget framework.
2. Treat SQL widget bases (`OWBaseSql`, SQL input decorators, credentials) as optional cross-cutting widget support. Do not require live PostgreSQL/MSSQL services for the minimum GUI/framework workflow.
3. Do not point future agents to source-checkout scripts or docs. Use the bundled references and bundled `scripts/create_widget_catalog.py`; the references below distill the needed framework behavior.
4. In headless Linux/CI, set `QT_QPA_PLATFORM=offscreen` before widget previews, widget tests, workflow loads, or catalog icon rendering.
5. For long-running widgets, use cooperative cancellation (`ConcurrentWidgetMixin`, `TaskState.is_interruption_requested()`) and call `shutdown()` from `onDeleteWidget()`.

## Evidence snapshot

Distilled and live-checked against Orange3 `3.41.0.dev` with Qt/PyQt available. Key verified API facts include:

- `OWWidget(*args, captionTitle=None, **kwargs)`
- `Input(name, type, ..., multiple=False, default=False, explicit=False, auto_summary=None, closing_sentinel=None)`
- `Output(name, type, ..., default=False, explicit=False, dynamic=True, auto_summary=None)`
- `WidgetPreview(widget_cls).run(input_data=None, *, no_exec=False, no_exit=False, **kwargs)`
- `DomainContextHandler(*, match_values=0, first_match=True, **kwargs)`
- `WidgetTest.create_widget(cls, stored_settings=None, reset_default_settings=True, **kwargs)`
- `ConcurrentWidgetMixin.start(task, *args, **kwargs)`, `cancel()`, and `shutdown()`

Representative source evidence was distilled from Orange widget/canvas framework modules, development docs, GUI/settings/testing helpers, workflow tests, SQL widget helpers, and the repo-maintained widget-catalog script. The runtime guidance here is self-contained and does not require those source files to be present.
