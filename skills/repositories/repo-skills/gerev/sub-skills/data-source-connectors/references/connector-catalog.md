# Built-in connector catalog

The table below condenses the built-in connectors that appear in the current repository.

| Connector | Config fields | Validation / auth check | Location selection | Notes |
| --- | --- | --- | --- | --- |
| Slack | `token` | `WebClient(...).auth_test()` | No | Uses bot token auth; fetches joined conversations and message history. |
| Confluence | `url`, `token` | `Confluence(...).get_all_spaces()` via retry wrapper | Yes | Self-hosted. Honors `CONFLUENCE_VERIFY_SSL` when set. |
| Confluence Cloud | `url`, `token`, `username` | Cloud `Confluence(...).get_all_spaces()` | Yes | Cloud auth uses username + API token. |
| Jira | `url`, `token` | `Jira(...).get_all_priorities()` | Yes | Self-hosted. Honors `JIRA_VERIFY_SSL` when set. |
| Jira Cloud | `url`, `token`, `username` | Cloud Jira client lists projects | Yes | Cloud auth uses username + token. |
| Google Drive | `json_str` | Service account JSON parse + Drive auth | No | Accepts a JSON string pasted into the UI textarea; supports docs/docx/pptx/pdf MIME types. |
| BookStack | `url`, `token_id`, `token_secret` | `get_all_books()` | No | Uses token id/secret auth and may retry on transient API failures. |
| Mattermost | `url`, `token` | `login()` | No | Parses the URL into scheme/host/port and indexes joined channels. |
| Rocket.Chat | `url`, `token_id`, `token_secret` | `me().json()` | No | Uses user id + token secret. |
| GitLab | `url`, `access_token` | membership-project query | No | Reads member-access projects and issues; no location selector in the current code. |

## Shared behavior worth remembering

- All connectors inherit `locations_to_index` from `BaseDataSourceConfig`, but only Jira and Confluence variants expose actual location selection in the UI.
- `get_display_name()` controls the human-readable label shown in the add-source panel.
- The UI falls back to a default icon if a connector-specific icon file is missing.
- Invalid config should raise the repo's connector-specific exception type, not a silent success.
