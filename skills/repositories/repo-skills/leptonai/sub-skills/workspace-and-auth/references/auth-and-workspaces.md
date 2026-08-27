# Auth and Workspaces

This reference covers the workspace-auth layer only: selecting a workspace, storing or reading workspace records, choosing environment overrides, and validating the context without exposing tokens.

## Mental model

Lepton has two auth contexts that can disagree:

| Context | Used by | What it contains | Notes |
|---|---|---|---|
| Persisted workspace record | `lep workspace ...`, `lep login`, and `WorkspaceRecord.client()` | Workspace id, API URL, display name when known, auth token, origin URL, token expiry when known, and one current workspace id | The CLI verifies a login with `APIClient.info()` before it persists or switches records. |
| Environment fallback | `APIClient()` and `WorkspaceRecord.login_with_env()` when called by a program | `LEPTON_WORKSPACE_ID`, optional `LEPTON_WORKSPACE_TOKEN`, optional `LEPTON_WORKSPACE_URL`, optional `LEPTON_WORKSPACE_ORIGIN_URL` | Environment variables do not automatically make `lep workspace status/id/url` use that context; those commands read the persisted current record. |

Use the persisted record for interactive CLI operation. Use environment variables for scripts, notebooks, services, CI, or deployments where a record should not be required.

## Safe CLI command map

| Goal | Command | Does it use credentials? | Token-safety notes |
|---|---|---:|---|
| Browser/prompt login | `lep login` | Yes | Opens a credential page when credentials are not passed. The user pastes `<workspace_id>:<auth_token>` into the prompt. |
| Direct login with credential string | `lep login -c '<workspace_id>:<auth_token>'` | Yes | Secret-bearing shell history risk. Prefer secure prompt or environment handling when possible. |
| Login/switch a specific workspace | `lep workspace login -i <workspace_id> -t '<auth_token>'` | Yes | Verifies access before persisting. For an already stored workspace id, omitted token/URL values fall back to the stored record. |
| Login with a custom API URL | `lep workspace login -i <workspace_id> -t '<auth_token>' --workspace-url <workspace_api_url>` | Yes | Use when the token was issued for a different Lepton environment than the default gateway. |
| List known workspaces | `lep workspace list` | May use credentials | Displays masked tokens and expiry. It may refresh missing expiry metadata, so treat as credentialed/read-only. |
| Show current workspace status | `lep workspace status` | Yes | Calls workspace info and prints state, tier, version, usage, and quota. |
| Print current workspace id | `lep workspace id` | No live API call | Prints the id from the current persisted record. Safe alternative to printing a token. |
| Print current workspace URL | `lep workspace url` | No live API call | Prints the URL from the current persisted record. Use to diagnose URL mismatches. |
| Logout current workspace | `lep logout` or `lep workspace logout` | Local record mutation | Clears the current workspace selection but keeps stored credentials unless `--purge` is used. |
| Purge current workspace credential | `lep logout --purge` or `lep workspace logout --purge` | Local record mutation | Removes the current workspace record. Use when a token is invalid or expired and should not remain stored. |
| Remove a workspace record | `lep workspace remove -i <workspace_id>` | Local record mutation | Removes that record; if it was current, the CLI is logged out. |

Avoid `lep workspace token` during ordinary troubleshooting. It prints the raw current token by design; use `id`, `url`, `list`, or `status` unless raw-token retrieval is the explicit user goal.

## Login behavior that matters

- `lep login` with `-c` splits the credential string at the first colon into `workspace_id` and `auth_token`.
- `lep login` without credentials opens a browser to a credential page, asks the user to paste `<workspace_id>:<auth_token>`, then validates the workspace before saving anything.
- `lep login` retries `APIClient.info()` on unauthorized responses for a fresh token propagation window before failing.
- `lep workspace login` validates access with `APIClient.info()` before persisting. Unlike the top-level login flow, it does not add the same long retry loop.
- Failed login attempts due to unauthorized, not-found, or forbidden workspace access do not call the persist step and do not switch the current workspace.
- `lep workspace login -i <workspace_id>` without `-t` only works when that workspace id is already in the local record. For a new id, provide a token.
- When logging in to an already stored workspace id, omitted token, URL, and origin URL values are inherited from the stored record. This preserves custom URLs during token refreshes.

## Environment fallback

`APIClient()` resolves auth context in this order:

| Field | Resolution order |
|---|---|
| Workspace id | Explicit `workspace_id` argument, then `LEPTON_WORKSPACE_ID`, then the current persisted workspace id. |
| Auth token | Explicit `auth_token` argument, then `LEPTON_WORKSPACE_TOKEN`, then the persisted token for the resolved workspace id. |
| API URL | Explicit `url` argument, then `LEPTON_WORKSPACE_URL`, then the persisted URL for the resolved workspace id, then the default workspace API URL for the id. |
| Origin URL | Explicit `workspace_origin_url` argument, then `LEPTON_WORKSPACE_ORIGIN_URL`, then the persisted origin URL for the resolved workspace id, then the derived origin URL for the API URL. |

Practical implications:

- `LEPTON_WORKSPACE_ID` alone is enough to choose the workspace id for `APIClient()`, but real calls still need a token from `LEPTON_WORKSPACE_TOKEN` or a persisted record for that same id.
- `LEPTON_WORKSPACE_URL` without the matching workspace id/token can accidentally combine one source of identity with another source of credentials. Clear unrelated variables before debugging a mismatch.
- `LEPTON_WORKSPACE_ORIGIN_URL` is an advanced override for the request `Origin` header. Do not set it unless the target environment requires it.
- `WorkspaceRecord.login_with_env()` persists the environment-supplied workspace context into the local record. Use it only when mutation of the local record is intended.

## Redaction patterns

Use these forms in all agent-visible summaries:

```text
workspace id: <workspace_id>
workspace url: <workspace_api_url>
auth token: <redacted-token>
credential string: <workspace_id>:<redacted-token>
Authorization: Bearer <redacted-token>
```

When copying CLI output, redact any raw token even if it appears in an error, traceback, shell trace, environment dump, or command line. Workspace ids and workspace API URLs may be necessary for diagnosis; tokens are not.
