---
name: data-source-connectors
description: "Manage Gerev data-source connectors, connector validation,
  location selection, and UI-backed add/remove flows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Gerev Data-Source Connectors

Use this sub-skill when a task involves adding, validating, listing, editing, or removing Gerev data sources. It also applies when you need to understand a connector's config schema, location-selection behavior, UI panel flow, or credential/setup notes.

## Best-fit tasks

- Add a new connector package under `app/data_source/sources/` and wire it into the dynamic loader.
- Debug `POST /api/v1/data-sources` failures caused by invalid credentials, missing services, or malformed config.
- Explain which connectors support location selection and how the UI asks for it.
- Understand the add/remove data-source flow from the React panel and the API contract it calls.
- Troubleshoot connector-specific validation, SSL, auth, or `locations_to_index` issues.

## Start here

1. Read [`data-source-api.md`](references/data-source-api.md) for the BaseDataSource contract, dynamic loading path, and UI/API flow.
2. Read [`connector-catalog.md`](references/connector-catalog.md) for the built-in connector catalog, config fields, auth patterns, and location-selection behavior.
3. Read [`ui-and-api-flows.md`](references/ui-and-api-flows.md) for concrete UI payload shapes and add/remove behavior.
4. Read [`troubleshooting.md`](references/troubleshooting.md) for invalid config, credential, SSL, and Pydantic-version failures.
5. Run the bundled [`inspect_data_sources.py`](scripts/inspect_data_sources.py) read-only helper when you want a quick source inventory:

   ```bash
   python scripts/inspect_data_sources.py --app-dir <checkout>/app --json
   ```

   Add `--strict` when you want a nonzero exit if required connector files are missing.

## High-signal routing checks

- `BaseDataSource.validate_config()` is async and must really connect to the service.
- `ConfigField` serialization currently depends on Pydantic v1-style behavior; newer Pydantic majors break connector metadata serialization.
- `DataSourceContext` dynamically discovers connector classes from `app/data_source/sources/` and stores connector types in the database.
- Only some connectors expose location selection. When `has_prerequisites` is true, the UI may prompt for extra setup before indexing.
- The UI data-source panel uses `/types`, `/connected`, `/{name}/list-locations`, `POST /data-sources`, and `DELETE /data-sources/{id}`.

## Boundaries

Included here: connector schemas, validation, location selection, connector discovery, UI add/remove behavior, and setup docs for the built-in sources.

Do not use this sub-skill for query ranking, Faiss/BM25 indexing, queue internals, Docker/image build, or frontend search-result rendering unless those details are needed only to explain connector flow.
