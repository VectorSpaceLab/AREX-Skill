# Index Extension

Ktem index extensions connect Kotaemon components to the application: they create resources, provide management UI, expose runtime settings, and return indexing/retrieval components when users upload or chat with indexed data.

## Index Surfaces

There are three common extension levels:

- **Override built-in file index pipelines** when the existing file collection UI/resources are enough but indexing or retrieval logic must change.
- **Customize built-in file index pages** when the upload/selector UI needs a different Gradio page class.
- **Create a new `BaseIndex` type** when the data source, lifecycle, resources, or management UI are different from the built-in file index.

Use `../../rag-core/SKILL.md` for the low-level vector retrieval/QA mechanics inside each pipeline. This page focuses on ktem registration and app contracts.

## Registration Points in `flowsettings.py`

App startup reads these keys:

```python
KH_INDEX_TYPES = [
    "ktem.index.file.FileIndex",
    "my_package.indexes.CustomIndex",
]

KH_INDICES = [
    {
        "name": "File Collection",
        "config": {"supported_file_types": ".pdf, .txt", "private": True},
        "index_type": "ktem.index.file.FileIndex",
    },
]
```

`KH_INDEX_TYPES` defines which index classes can be selected/created. `KH_INDICES` seeds actual index instances into the database if no index with that name exists.

For built-in `FileIndex`, these override keys are checked in order:

- `FILE_INDEX_PIPELINE` in an index instance config, then `FILE_INDEX_{id}_PIPELINE`, then global `FILE_INDEX_PIPELINE`, otherwise the default `ktem.index.file.pipelines.IndexDocumentPipeline`.
- `FILE_INDEX_RETRIEVER_PIPELINES` in config, then `FILE_INDEX_{id}_RETRIEVER_PIPELINES`, then global `FILE_INDEX_RETRIEVER_PIPELINES`, otherwise the default `DocumentRetrievalPipeline`.
- `FILE_INDEX_SELECTOR_UI` in config, then `FILE_INDEX_{id}_SELECTOR_UI`, then global `FILE_INDEX_SELECTOR_UI`, otherwise the default `FileSelector`.
- `FILE_INDEX_UI` in config, then `FILE_INDEX_{id}_UI`, then global `FILE_INDEX_UI`, otherwise the default `FileIndexPage`.

All values are dotted import strings. Lists such as `FILE_INDEX_RETRIEVER_PIPELINES` contain dotted class strings.

## `BaseIndex` Contract

Subclass `ktem.index.base.BaseIndex` when creating a new index type. The constructor receives `app`, `id`, `name`, and `config`. Important hooks:

- `on_create()` runs once when the index is first recorded; create tables, folders, collections, and normalize admin config here.
- `on_delete()` removes resources when the user deletes the index.
- `on_start()` runs at app startup; import pipeline/UI classes and initialize resources.
- `get_selector_component_ui()` returns a `BasePage` used by Chat to select indexed entities.
- `get_index_page_ui()` returns a `BasePage` used by the Resources/Index page to manage entities.
- `get_user_settings()` returns runtime settings surfaced in the Settings page.
- `get_admin_settings()` returns settings shown when creating/configuring an index.
- `get_indexing_pipeline(settings, user_id)` returns a `BaseComponent` that indexes entities.
- `get_retriever_pipelines(settings, user_id, selected)` returns retrieval components for chat.

`IndexManager` imports index classes with `import_dotted_string(..., safe=False)`, creates seeded indices from `KH_INDICES`, stores definitions in the SQL database, and calls `on_start()` for each existing entry during app startup.

## File Index Pipeline Contracts

The built-in file index resources include SQL `Source`, SQL `Index`, SQL `FileGroup`, a vector store, a document store, and a file storage directory. `FileIndex` assigns these resources to pipeline instances after `get_pipeline(...)` returns.

### Indexing Pipeline

Subclass `ktem.index.file.base.BaseFileIndexIndexing` and implement:

```python
def run(self, file_paths: str | Path | list[str | Path], *args, **kwargs) -> tuple[list[str | None], list[str | None]]:
    ...

@classmethod
def get_pipeline(cls, user_settings: dict, index_settings: dict):
    return cls(...)
```

Optional but common methods:

- `stream(...)` yields `Document` objects with `channel="index"` or `channel="debug"` and returns indexed ids, errors, and documents.
- `get_user_settings()` returns settings dictionaries for the Settings page.
- `copy_to_filestorage(...)` copies original files into the index storage directory.
- `rebuild_index()` supports admin rebuild operations when implemented.

`BaseFileIndexIndexing` fields assigned by `FileIndex`: `Source`, `Index`, `VS`, `DS`, `FSPath`, `user_id`, `private`, `chunk_size`, and `chunk_overlap`.

### Retriever Pipeline

Subclass `ktem.index.file.base.BaseFileIndexRetriever` and implement:

```python
@classmethod
def get_pipeline(cls, user_settings: dict, index_settings: dict, selected: list | None = None):
    return cls(...)

def run(self, text: str, doc_ids: list[str] | None = None, *args, **kwargs):
    ...
```

`BaseFileIndexRetriever` fields assigned by `FileIndex`: `Source`, `Index`, `VS`, `DS`, `FSPath`, and `user_id`.

Built-in `DocumentRetrievalPipeline` demonstrates common settings keys: `reranking_llm`, `num_retrieval`, `retrieval_mode`, `prioritize_table`, `mmr`, `use_reranking`, and `use_llm_reranking`.

## Settings Dictionary Shape

Settings methods return a dictionary where each key maps to a setting item compatible with `ktem.settings.SettingItem`:

```python
return {
    "top_k": {
        "name": "Number of chunks",
        "value": 8,
        "component": "number",
        "info": "How many chunks to retrieve before reranking.",
    },
    "mode": {
        "name": "Retrieval mode",
        "value": "hybrid",
        "choices": ["vector", "text", "hybrid"],
        "component": "dropdown",
    },
}
```

Supported ktem Settings components are `text`, `number`, `checkbox`, `dropdown`, `radio`, and `checkboxgroup`. Use `special_type: "llm"` or `special_type: "embedding"` when a setting should be refreshed from the app's model/resource managers.

For file indexes, flattened runtime keys use `index.options.<index_id>.<setting_key>`. `FileIndex` strips this prefix before passing settings into `get_pipeline(...)`.

## UI Class Overrides

File index selector/index UI classes should inherit `ktem.app.BasePage`. A page can:

- Build Gradio components in `on_building_ui()`.
- Declare public events by listing names in `public_events`.
- Subscribe to app events in `on_subscribe_public_events()`.
- Register Gradio event handlers in `on_register_events()`.
- Return components from `as_gradio_component()` when another page needs to wire them.

If overriding `FILE_INDEX_SELECTOR_UI`, provide a `get_selected_ids(selected)` method compatible with `FileIndex.get_retriever_pipelines(...)` because the file index calls it before constructing retrievers.

## Custom File Retriever with User Settings

A safe implementation plan for a custom retriever:

1. Subclass `BaseFileIndexRetriever`.
2. Add `get_user_settings()` with stable keys such as `custom_top_k` and `retrieval_mode`.
3. Implement `get_pipeline(user_settings, index_settings, selected)` and avoid reading `flowsettings.py` directly except for developer-only defaults.
4. Use assigned `VS`, `DS`, `Source`, `Index`, and `FSPath`; do not create separate stores unless the index config intentionally points to them.
5. Preserve selected document ids by calling `set_run({".doc_ids": selected}, temp=False)` or accepting selected ids through the `run(...)` call.
6. Register the class through `FILE_INDEX_RETRIEVER_PIPELINES = ["my_package.retrievers.CustomRetriever"]` or per-index config.

## Common Review Assertions

- Dotted paths point to classes and are importable from the same working directory used to start the app.
- Indexing classes implement `run(file_paths, ...)` and `get_pipeline(user_settings, index_settings)`.
- Retriever classes implement `get_pipeline(user_settings, index_settings, selected)` and a query-facing `run(...)`.
- `get_user_settings()` returns setting item dictionaries, not already-flattened values.
- `KH_INDICES[*].index_type` values are also present in or importable like `KH_INDEX_TYPES`.
- New `BaseIndex` subclasses do not drop, overwrite, or reuse built-in file index tables unintentionally.
