# Data Managers and Tool Data Tables

Galaxy data managers are admin-only tools that create or download persistent reference data and add rows to tool data tables. They bridge three layers: a data-manager tool, a data-manager XML configuration, and one or more tool-data table definitions backed by `.loc` files or equivalent table entries.

## Concepts

- Tool data lives under the configured tool-data area by default; data-manager-created files can be separated with the data-manager data path setting.
- `.loc` files are usually tab-separated rows containing IDs, display names, dbkeys, paths, and tool-specific metadata.
- Tool data table config XML declares table names, columns, separators/comment behavior, duplicate handling, and files or URLs that provide rows.
- Tool Shed-installed tables are tracked separately from local table config and can have versioned repository metadata.
- Multiple table declarations with the same name can be merged, so column shape consistency matters more than file location alone.

## Data Manager XML Contract

A data-manager configuration contains a root `data_managers` element, one or more `data_manager` entries, and `data_table` entries describing which tool data table receives rows.

Review each XML file for:

- `data_manager` has a unique stable `id` and `tool_file` pointing to the data manager tool definition.
- Each `data_table` `name` matches an existing table definition or an intentional new table.
- `output` columns match the JSON keys produced by the tool.
- `move` rules copy files from the output dataset’s extra-files area into the configured data-manager data path.
- `source`, `target`, and value translations are single-line templates and cannot escape intended storage roots.
- `value_translation` order is intentional; moves happen before translations.

## JSON Output Contract

A data-manager tool reports new entries by writing JSON with a top-level `data_tables` object. Each table name maps either to a list of row dictionaries or to an object with `add` and `remove` lists.

Common row keys include `value`, `dbkey`, `name`, and `path`, but the exact keys must match the table’s configured columns. Preserve stable IDs and append new versioned rows when possible instead of mutating existing production entries.

Input parameter JSON may be provided to data-manager tools so the executable can inspect job parameters, output data paths, tool-data paths, user/admin context, and configured data table helpers. Treat that JSON as runtime context, not a public schema for arbitrary external callers.

## Tool Data Table Review

When adding or debugging a table:

1. Confirm the table `name` used by tool XML `from_data_table` options matches the table config.
2. Confirm the `columns` order matches each `.loc` row and any filter column indexes used by tools.
3. Confirm required columns such as `value`, `dbkey`, `name`, and `path` are present when the consuming tool expects them.
4. Confirm paths are absolute or correctly relative to the configured tool-data root.
5. Confirm `.loc.sample` files use the same column count as production rows.
6. For shared tables, use globally unique `value` IDs and controlled vocabularies where documented.

For example, shared model tables should avoid tool-specific `free_tag` values unless the tag is a documented cross-tool narrowing convention, and should prefer adding rows over removing or rewriting rows that older tools may still reference.

## Testing and Validation

Use tool tests for the data manager tool behavior and static XML/JSON checks for the table contract. A useful review plan includes:

- XML parse of data-manager config and data table config.
- JSON schema sanity: top-level `data_tables`, expected table names, row dictionaries, and no trailing commas.
- Fixture row validation against configured table columns.
- A tool test that exercises the data-manager tool output without requiring a real large download when possible.
- Admin/server-backed data-manager tests only when the user explicitly provides a disposable Galaxy instance or confirms use of the repository’s integration test harness.

Route generic tool wrapper mechanics to [Workflows and Tools](../../workflows-and-tools/SKILL.md); keep this reference focused on persistent table and data-manager contracts.
