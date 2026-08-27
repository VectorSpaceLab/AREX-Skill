# Gerev data-source API and discovery flow

This reference summarizes the connector contract and the runtime path the app uses to discover, validate, and manage data sources.

## Base connector contract

Every connector inherits from `BaseDataSource` and must provide these behaviors:

| Member | Purpose | Notes |
| --- | --- | --- |
| `get_config_fields()` | Describe the UI form for the connector | Return `ConfigField` objects with `name`, `label`, `placeholder`, and `input_type`. |
| `validate_config(config)` | Validate the user-supplied config | Async. Must actually connect or auth-check the service; do not accept purely syntactic validation. |
| `_feed_new_documents()` | Add new documents or tasks to the indexing queue | Connector-specific document fetch loop. |

Shared helpers and defaults:

- `BaseDataSourceConfig` includes `locations_to_index: List[Location] = []`.
- `BaseDataSource.get_display_name()` converts `SomethingDataSource` to `Something` for the UI.
- `BaseDataSource.has_prerequisites()` defaults to `False` and is used by the UI to show extra setup instructions.
- `BaseDataSource.list_locations()` defaults to an empty list.

## Dynamic loading and persistence

`DataSourceContext` owns connector discovery and persistence.

1. `DynamicLoader.find_data_sources()` walks `app/data_source/sources/` and identifies classes that inherit from `BaseDataSource`.
2. `DataSourceContext._load_data_source_classes()` loads the Python classes, saves `DataSourceType` rows, and serializes each connector's config fields.
3. `DataSourceContext.create_data_source()`:
   - resolves the connector class,
   - awaits `validate_config(config)`,
   - writes the `DataSource` row,
   - caches the connector instance.
4. `DataSourceContext.delete_data_source()` removes the row and cache entry.
5. `DataSourceContext.get_data_source_classes()` and `get_data_source_class()` power the `GET /api/v1/data-sources/types` route.

## UI and API flow

The React panel talks to the following routes:

| Route | Caller use | Notes |
| --- | --- | --- |
| `GET /api/v1/data-sources/types` | Populate the connector picker | Returns display name, icon, config fields, and `has_prerequisites`. |
| `GET /api/v1/data-sources/connected` | Show active sources | Used to render active badges and edit mode. |
| `POST /api/v1/data-sources/{name}/list-locations` | Ask a connector for location choices | Only useful when a connector implements location listing. |
| `POST /api/v1/data-sources` | Create and start indexing a source | Adds the source and queues indexing. |
| `DELETE /api/v1/data-sources/{id}` | Remove a source | Deletes the source and its documents. |

## Connector-specific location behavior

Only a subset of connectors implement `list_locations`:

- Jira self-hosted and Jira Cloud return project lists.
- Confluence self-hosted and Confluence Cloud return space lists.
- Other built-in connectors index everything they can reach and do not ask for a location selector in the UI.

## Source paths that matter

- `app/data_source/api/base_data_source.py`
- `app/data_source/api/context.py`
- `app/data_source/api/dynamic_loader.py`
- `app/api/data_source.py`
- `ui/src/components/data-source-panel.tsx`
- `ui/src/api.ts`
- `ui/src/data-source.ts`
