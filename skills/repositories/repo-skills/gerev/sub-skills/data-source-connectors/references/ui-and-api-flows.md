# UI and API flows for Gerev data sources

Use this reference when a task involves the Data Source Panel, API payloads, or adding a new connector to the UI.

## Frontend API base

The frontend creates one Axios client with base URL:

```text
{window.location.protocol}//{window.location.hostname}:{port}/api/v1
```

- In development, `port` is `8000`.
- In production, `port` is the current browser port.
- Data-source API calls in the UI therefore use paths like `/data-sources/types` relative to `/api/v1`.
- The UI sends a `uuid` header from local storage for telemetry. It is not part of connector authentication.

## Initial UI state

The app loads connector metadata and connected sources independently:

1. `GET /data-sources/types`
   - Response is converted to a dictionary keyed by `DataSourceType.name`.
   - The Data Source Panel builds select options from this dictionary.
2. `GET /data-sources/connected`
   - Response populates the active-source chips in the panel.

Expected TypeScript shapes:

```ts
interface ConfigField {
  name: string
  input_type: "text" | "textarea" | "password"
  label: string
  placeholder: string
  value?: string
}

interface DataSourceType {
  name: string
  display_name: string
  config_fields: ConfigField[]
  image_base64: string
  has_prerequisites: boolean
}

interface ConnectedDataSource {
  id: number
  name: string
}

interface IndexLocation {
  value: string
  label: string
}
```

## UI add flow

1. User opens the Data Source Panel.
2. Panel shows active connected sources and unconnected source chips.
3. User selects a source to add.
4. Panel renders source-specific instructions, then renders one input for each `config_fields` entry:
   - `text` and `password` render as single-line inputs.
   - `textarea` renders as a large multi-line box.
5. Panel builds a plain config object by assigning `config[field.name] = field.value`.
6. If `has_prerequisites` is false, submit immediately.
7. If `has_prerequisites` is true and locations have not yet been listed:
   - Call `POST /data-sources/{source_id}/list-locations` with the config object.
   - Store the returned `IndexLocation[]`.
   - Show a multi-select for locations.
8. User selects one or more locations and proceeds, or clicks "Index everything".
9. Panel always adds `locations_to_index` to the config before final submit.
10. Final submit calls `POST /data-sources` with `{name, config}`.
11. On success, the UI receives the new numeric ID, clears field values, updates connected sources, and shows an indexing toast.

### API example: list locations

```bash
curl -sS \
  -H 'Content-Type: application/json' \
  -X POST \
  'http://localhost:8000/api/v1/data-sources/confluence/list-locations' \
  --data '{"url":"https://confluence.example.test","token":"REDACTED"}'
```

Expected response shape:

```json
[
  {"value": "ENG", "label": "Engineering"},
  {"value": "OPS", "label": "Operations"}
]
```

### API example: add with selected locations

```bash
curl -sS \
  -H 'Content-Type: application/json' \
  -X POST \
  'http://localhost:8000/api/v1/data-sources' \
  --data '{
    "name": "jira",
    "config": {
      "url": "https://jira.example.test",
      "token": "REDACTED",
      "locations_to_index": [
        {"value": "ENG", "label": "Engineering"}
      ]
    }
  }'
```

Expected response body: the created data-source ID as an integer.

### API example: add and index everything

For a location-backed connector, send an empty array or omit `locations_to_index` to index all accessible locations. The UI sends an empty array when "Index everything" is chosen.

```json
{
  "name": "confluence_cloud",
  "config": {
    "url": "https://example.atlassian.net/wiki",
    "username": "agent@example.test",
    "token": "REDACTED",
    "locations_to_index": []
  }
}
```

## UI remove flow

1. User toggles edit mode in the Data Source Panel.
2. User clicks the remove icon on a connected source.
3. The panel shows a confirmation prompt.
4. Before sending a delete request, the UI blocks removal if:
   - indexing is currently in progress; or
   - another removal is already in progress.
5. On confirmation, call `DELETE /data-sources/{id}`.
6. On success, remove the source from UI state and leave edit mode when no connected sources remain.

Backend deletion behavior:

- `DataSourceContext.delete_data_source(id)` verifies the source exists.
- The data-source row is deleted.
- Related documents are cascaded through the SQLAlchemy relationship and index cleanup hook.
- The indexed-count signal is reset.

## Built-in setup prompts shown in the UI

| Source | UI guidance summary |
| --- | --- |
| Slack | Copy the provided app manifest, create a Slack app from manifest, install it to the workspace, then copy the Bot User OAuth Token. |
| Confluence self-hosted | Profile/settings -> Personal Access Tokens -> create token with automatic expiry unchecked. |
| Jira self-hosted | Profile/settings -> Personal Access Tokens -> create token with automatic expiry unchecked. |
| Confluence Cloud / Jira Cloud | Atlassian account security -> API tokens -> create and copy token; also provide username/email. |
| Google Drive | Follow service-account setup: create project, enable Drive API, create service account + JSON key, share folders with service-account email, paste JSON content. |
| BookStack | Profile -> Edit profile -> API tokens -> create token, set long expiry, copy token ID and secret. |
| Mattermost | Profile -> Security -> Personal Access Tokens -> create token; personal access tokens must be enabled by the server. |
| Rocket.Chat | My Account -> Personal Access Tokens -> ignore 2FA, create token, copy token and user ID; URL must include scheme. |
| GitLab | Preferences -> Access Tokens -> remove expiration if desired, enable `read_api`, create and copy token. |

## Adding a connector to the UI

Backend discovery alone makes a connector appear in `/data-sources/types` if the class and config fields load successfully. For a polished UI-backed flow, also update:

1. **Instructions**: Add a conditional block keyed by `selectedDataSource.value === '<source_id>'` in the Data Source Panel.
2. **Icon**: Add an image named `<source_id>.png` under the app's data-source icon directory. If absent, the backend falls back to the default icon.
3. **Location UX**: Override `has_prerequisites()` to return `True` only when the user should be forced through a `list-locations` step before adding.
4. **Config fields**: Choose `text`, `password`, or `textarea` based on the secret shape. Use `textarea` for full JSON file contents such as Google Drive's `json_str`.
5. **Errors**: Keep connector validation exceptions actionable; the UI surfaces the backend response text in toasts.

## Safe checks before live validation

- Run `sub-skills/data-source-connectors/scripts/inspect_data_sources.py --app-dir app` from the generated skill tree root against the target checkout to inspect class names and config fields without importing the app or calling services.
- Confirm the source ID in payloads matches the discovered snake-case ID.
- Confirm the config keys match the `ConfigField.name` values, not the UI labels.
- Do not call `validate_config`, `list-locations`, or final add endpoints unless the task has credentials, network permission, and the user expects live service access.
