# Plugin and UI Extension

Ktem extensions can be ordinary Python modules referenced by `flowsettings.py`, page classes integrated into the app lifecycle, or packaged pluggy plugins discovered through the `ktem` entry point namespace.

## App Lifecycle Mental Model

`ktem.app.BaseApp` initializes in this order:

1. Reads app identity, feature flags, theme assets, and default settings.
2. Creates `SettingGroup` for application, reasoning, and index settings.
3. Calls `register_extensions()` to load pluggy declarations.
4. Calls `register_reasonings()` to import `KH_REASONINGS` classes and add reasoning settings.
5. Calls `initialize_indices()` to create/start indices and add index settings.
6. Finalizes reasoning/index groups and creates the Gradio `settings_state`.

When the app UI is built, page objects declare public events, subscribe to events, register handlers, and run `on_app_created()` callbacks.

## `BasePage` Contract

Subclass `ktem.app.BasePage` for custom pages, selector UIs, index management UIs, or page fragments. Useful methods:

- `on_building_ui()` creates Gradio components.
- `public_events` lists event names this page declares.
- `on_subscribe_public_events()` subscribes to events declared by the app or other pages.
- `on_register_events()` wires Gradio event handlers.
- `_on_app_created()` runs after all pages and events are created.
- `as_gradio_component()` returns one or more components when another page needs to use them.
- `render()`/`unrender()` recursively render nested Gradio blocks and child pages.

Events are registered through the app with `declare_event(name)`, `subscribe_event(name, definition)`, and `get_event(name)`. A missing event raises `HookNotDeclared`; re-declaring an existing event raises `HookAlreadyDeclared`.

## Settings Page Integration

Settings are rendered from `SettingItem` dictionaries. The ktem Settings page supports:

- Single-value components: `text`, `number`, `checkbox`.
- Choice components: `dropdown`, `radio`, `checkboxgroup`.

A setting item may include `name`, `value`, `choices`, `metadata`, `component`, and `special_type`. `special_type` values such as `llm` and `embedding` are used to refresh model-related choices.

Where settings appear:

- `SETTINGS_APP` entries render under the General tab when SSO does not hide settings.
- Reasoning settings render under the Reasoning tab; available modes come from `KH_REASONINGS` plus pluggy reasoning declarations.
- Index settings render under Retrieval settings; each index receives its own subtab and keys flatten as `index.options.<index_id>.<setting_key>`.

If a custom setting does not appear, check that the corresponding `get_user_settings()` method is called during app startup, returns non-empty `SettingItem`-shaped dictionaries, and uses supported `component` ids.

## Pluggy Extension Protocol

Ktem defines a pluggy namespace named `ktem`. A packaged extension should import the marker and implement the hook:

```python
from ktem.extension_protocol import hookimpl


@hookimpl
def ktem_declare_extensions() -> dict:
    return {
        "id": "my-extension",
        "name": "My Extension",
        "version": "0.1.0",
        "support_host": "ktem",
        "functionality": {
            "reasoning": {
                "my-reasoning": {
                    "name": "My Reasoning",
                    "callbacks": {},
                    "settings": {},
                }
            },
            "index": {
                "name": "My Index",
                "callbacks": {
                    "get_index_pipeline": make_index_pipeline,
                    "get_retrievers": {"default": make_retriever},
                },
                "settings": {},
            },
        },
    }
```

The hook is called with no arguments. It returns a dictionary with an extension id, human name, version, support host, and functionality declaration.

Ids inside the declaration must not contain `.` or `/`. App startup prefixes pluggy reasoning ids with `<extension_id>/<reasoning_id>` when adding settings, so choose stable ids that are safe in UI paths.

In this checkout, `BaseApp.register_extensions()` loads setuptools entry points for `ktem`, reads declarations, and currently wires declared reasoning settings into `default_settings.reasoning.options`. Treat index callback support in the protocol as forward-looking unless the target checkout has code that consumes those callbacks.

## Packaging a Pluggy Extension

For setuptools-style packages, expose the plugin module through an entry point named under the `ktem` group. Example shape:

```python
setup(
    name="my-ktem-extension",
    entry_points={
        "ktem": ["my_extension = my_package.plugin"],
    },
)
```

Keep plugin imports light. App startup loads entry points before indices initialize, so avoid importing provider clients, opening databases, downloading models, or reading user files at module import time. Delay expensive work until callbacks or pipeline construction.

## Project Template Integration

The default project template creates a package with `setup.py`, README, tests, and a `pipeline.py` containing component examples. After generating a project:

1. Replace placeholder provider endpoints and dummy keys with environment-driven configuration or app managers.
2. Install the project editable in the same environment that runs ktem.
3. Add the pipeline's dotted class path to `KH_REASONINGS`, `FILE_INDEX_PIPELINE`, `FILE_INDEX_RETRIEVER_PIPELINES`, or `KH_INDEX_TYPES` as appropriate.
4. Run the static checker on the project directory before launching the app.
5. Start the app only after the dotted path can be imported from a Python shell in the app working directory.

A template directory should include packaging metadata (`setup.py` or `pyproject.toml`), a Python package directory with `__init__.py`, and at least one component class with `run(...)`.

## UI and Settings Review Tips

- Page constructors in built-in code often call `on_building_ui()` immediately; avoid double-building when subclassing.
- Event names should be stable and unique enough to avoid collisions with built-in page events.
- Do not mutate `settings_state` shape manually; add settings through the relevant default settings group.
- Choice settings should supply choices in the shape expected by Gradio: either simple values or `(label, value)` pairs.
- Avoid storing secrets in setting defaults or logs. Use provider/resource managers and redact secrets when diagnosing.
- Keep file paths in settings portable; prefer app data dirs and index resources over absolute developer-machine paths.

## Cross-Links

- Use `component-development.md` for `BaseComponent`, prompt UI, and class-level settings.
- Use `index-extension.md` for file index override keys and `BaseIndex` lifecycle.
- Use `../../app-deployment/SKILL.md` for operational launch and environment setup.
- Use `../../model-providers/SKILL.md` for model manager entries used by custom settings.
