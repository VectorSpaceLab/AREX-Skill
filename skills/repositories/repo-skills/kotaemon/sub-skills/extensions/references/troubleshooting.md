# Extension Troubleshooting

Use this reference when a custom Kotaemon/ktem component, index, UI page, pluggy package, or scaffolded project does not register or behave as expected.

## Static Check First

Run the bundled checker before importing new extension code in a live app:

```bash
python scripts/scaffold_component_check.py --path <component-file-or-template-dir>
```

The checker parses Python and text files only. It does not import project code, start Gradio, read user data, or execute plugin callbacks.

## Component Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Component class is not visible to prompt UI or pipeline tooling | Class does not subclass `BaseComponent`, or the file contains only helper functions | Add a concrete class that subclasses `kotaemon.base.BaseComponent` or a more specific Kotaemon/ktem base class. |
| Component instantiates but calling it fails | Missing `run(...)`, incompatible `run` parameters, or required fields have no defaults | Implement `run(...)` with the caller's expected inputs and make required params explicit in constructor docs or settings. |
| Nested components are not inspected as nodes | Child fields lack type annotations or are stored dynamically | Declare params and child components as annotated class fields; use `Param(..., ignore_ui=True)` for non-user-facing values. |
| Prompt UI exposes secrets or large objects | Sensitive fields are plain params | Use `Param(..., ignore_ui=True)`, load secrets from provider/resource managers, and redact diagnostics. |

## Flowsettings and Dotted Paths

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Startup fails with an import error for a custom class | Dotted path points to a module, typo, or package not installed in the app environment | Install the extension package editable, then test `python -c "from package.module import Class"` before editing config. |
| Reasoning mode does not appear | Class is absent from `KH_REASONINGS`, `get_info()` is missing, or `get_info()["id"]` collides | Register the full dotted class path and provide stable `id`, `name`, and `description` fields. |
| File index override is ignored | Wrong override key or per-index/global precedence confusion | Use `FILE_INDEX_PIPELINE`, `FILE_INDEX_RETRIEVER_PIPELINES`, `FILE_INDEX_SELECTOR_UI`, or `FILE_INDEX_UI`; prefer per-index config when only one index should change. |

## Index Extension Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Upload works but retrieval returns nothing | Indexing pipeline wrote docs without matching vector/docstore ids, or retriever ignores selected ids | Preserve ids when writing both stores and honor `selected`/`doc_ids` in retrievers. |
| Settings do not appear in Retrieval settings | `get_user_settings()` returns flattened values or unsupported component ids | Return `SettingItem`-shaped dictionaries with supported components: `text`, `number`, `checkbox`, `dropdown`, `radio`, or `checkboxgroup`. |
| Custom index crashes on startup | `on_start()` imports heavy provider clients, starts services, or assumes files exist | Keep startup light; validate external resources lazily in `get_indexing_pipeline(...)` or `get_retriever_pipelines(...)`. |
| Admin-created index loses resources on delete | `on_delete()` deletes broad paths or shared stores | Scope deletion to this index id/config and protect shared app data. |

## Pluggy and UI Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Pluggy extension is not discovered | Missing `ktem` entry point or plugin module import fails | Add a setuptools entry point under group `ktem` and keep module-level imports lightweight. |
| Hook declaration is ignored | Function lacks `@hookimpl` or returns an unexpected dictionary shape | Implement `ktem_declare_extensions()` with `id`, `name`, `version`, `support_host`, and `functionality`. |
| App raises `HookNotDeclared` | Page subscribes to an event before any page declares it | Declare public events on the owner page, then subscribe from dependent pages during event subscription. |
| App raises `HookAlreadyDeclared` | Two pages declare the same event name | Prefix custom event names with the extension or page id. |

## Template and Scaffold Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Generated project cannot be installed | Template lacks `setup.py`/`pyproject.toml` or a package directory with `__init__.py` | Add packaging metadata and a real import package before referencing dotted paths. |
| Template creates a pipeline but app cannot find it | Class name/path changed after generation | Update the dotted path in `flowsettings.py` and rerun the static checker on the generated project. |
| Tests pass but app startup fails | Tests import from the checkout while app runs from an installed package | Verify importability from the same working directory and Python environment used to launch the app. |

## Hard Cases to Support

- **Custom file retriever with settings**: verify the retriever subclasses the file retriever base, exposes stable `get_user_settings()` keys, preserves selected document ids, and registers through a `FILE_INDEX_RETRIEVER_PIPELINES` dotted class list.
- **New component/template review**: check for packaging metadata, an importable package, a `BaseComponent` subclass with `run(...)`, safe defaults, and no provider/network side effects at import time.
