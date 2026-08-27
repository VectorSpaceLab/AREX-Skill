# Data-source connector troubleshooting

## Invalid config or auth failures

Symptoms:

- `POST /api/v1/data-sources` returns an error message from the connector.
- The UI panel rejects a token, URL, or JSON blob.
- Validation reaches the remote service and then fails.

Likely causes:

- expired or revoked token
- wrong URL or missing scheme
- missing service-account JSON fields for Google Drive
- username/token pairing mismatch for cloud Atlassian connectors
- insufficient permissions or scopes on the remote service

Recovery:

1. Re-check the connector-specific setup doc.
2. Use the bundled catalog to confirm the exact config fields.
3. Re-run the validation path from the app rather than trusting a syntactic check.

## Location listing failures

Symptoms:

- the UI never shows a location picker
- `/{name}/list-locations` fails
- the connector has `has_prerequisites = True` but still cannot list locations

Likely causes:

- missing credentials or permissions
- empty account membership on the target service
- SSL verification problems for self-hosted Atlassian connectors
- `locations_to_index` not populated when the connector expects it

Recovery:

- Jira and Confluence are the only built-in connectors that currently return selectable locations.
- Re-check `JIRA_VERIFY_SSL` or `CONFLUENCE_VERIFY_SSL` for self-hosted instances.
- Make sure the service account or token has access to at least one project/space.

## Pydantic version drift

`ConfigField` serialization currently depends on older Pydantic behavior. If the app starts failing while enumerating connector types, pin back to Pydantic v1-compatible versions and recheck `GET /api/v1/data-sources/types`.

## UI panel confusion

Symptoms:

- the connector list loads, but the form fields look wrong or missing
- the panel shows a default icon for every connector
- the add/remove buttons do not map to the expected connector

Recovery:

- confirm the backend returned the correct `name`, `display_name`, `config_fields`, and `has_prerequisites` values
- check the UI route contract in `../../../references/frontend-api.md`
- verify the connector class name matches the dynamic loader's `<Platform>DataSource` naming rule
