# API Client Workspace Context

Use `leptonai.api.v2.client.APIClient` when Python code needs the workspace API context that backs Lepton CLI operations. This is not the high-level dynamic endpoint caller; use the SDK/client sub-skill for endpoint invocation patterns.

## Constructor

```python
from leptonai.api.v2.client import APIClient

client = APIClient(
    workspace_id=None,
    auth_token=None,
    url=None,
    workspace_origin_url=None,
)
```

The constructor accepts explicit values, environment fallback, or persisted workspace-record fallback. The first argument may also be a credential string in `<workspace_id>:<auth_token>` form when `auth_token` is not separately provided.

## Resolution order

`APIClient()` chooses context in this order:

1. Workspace id: explicit argument, then `LEPTON_WORKSPACE_ID`, then the current persisted workspace record.
2. Token: explicit argument, then `LEPTON_WORKSPACE_TOKEN`, then the persisted token for the resolved workspace id.
3. API URL: explicit argument, then `LEPTON_WORKSPACE_URL`, then the persisted URL for the resolved workspace id, then the default workspace API URL for the workspace id.
4. Origin URL: explicit argument, then `LEPTON_WORKSPACE_ORIGIN_URL`, then the persisted origin URL for the resolved workspace id, then a derived origin URL from the API URL.

If no workspace id can be resolved, construction raises a workspace configuration error and tells the user to specify `workspace_id`, set `LEPTON_WORKSPACE_ID`, or use `lep login`.

## Headers and token safety

- When a token is present, requests carry `Authorization: Bearer <redacted-token>`.
- When `workspace_origin_url` is present, requests carry an `origin` header.
- Do not log `client.auth_token`, `client.token()`, request headers, or environment variables containing token values.
- `APIClient.info()` masks token hints in workspace access exceptions; preserve that masking when summarizing failures.

## Safe validation snippet

This checks workspace reachability without printing secrets. It performs a read-only workspace-info request, so run it only when the user has allowed credentialed validation.

```python
import os
from leptonai.api.v2.client import APIClient

client = APIClient(
    workspace_id=os.environ.get("LEPTON_WORKSPACE_ID"),
    auth_token=os.environ.get("LEPTON_WORKSPACE_TOKEN"),
    url=os.environ.get("LEPTON_WORKSPACE_URL"),
    workspace_origin_url=os.environ.get("LEPTON_WORKSPACE_ORIGIN_URL"),
)
info = client.info()
print({
    "workspace_id": client.get_workspace_id(),
    "workspace_name": getattr(info, "workspace_name", None),
    "state": getattr(info, "workspace_state", None),
    "tier": getattr(info, "workspace_tier", None),
})
```

Do not print the token before or after this snippet. If the caller only needs context diagnosis, prefer the bundled context checker first.

## `WorkspaceRecord` helpers

| Helper | Purpose | Notes |
|---|---|---|
| `WorkspaceRecord.current()` | Return the current persisted workspace info or `None`. | Used by `lep workspace id/url` and as a fallback for `APIClient()`. |
| `WorkspaceRecord.workspaces()` | Return all persisted workspace records. | `lep workspace list` renders these with masked tokens and expiry. |
| `WorkspaceRecord.has(workspace_id)` / `get(workspace_id)` | Check/read one persisted record. | Useful before switching to an existing workspace id without re-entering a token. |
| `WorkspaceRecord.client(workspace_id=None)` | Build `APIClient` from a persisted record. | Raises if no current workspace is set or if the requested id is not in the record. |
| `WorkspaceRecord.set_or_exit(...)` | Persist a record from CLI code. | CLI login calls this only after `APIClient.info()` succeeds. |
| `WorkspaceRecord.logout(purge=False)` | Clear current selection; optionally remove the current record. | `--purge` deletes the token-bearing record. |
| `WorkspaceRecord.remove(workspace_id)` | Delete one persisted workspace record. | Clears current selection if the removed id was current. |
| `WorkspaceRecord.refresh_token_expires_at(...)` | Fetch and store token expiry when available. | Expiry metadata may be unavailable; absence does not prove validity. |

## Workspace access exceptions

`APIClient.info()` maps workspace-info HTTP status codes to typed failures:

| HTTP status | Exception | Most likely meaning | First response |
|---:|---|---|---|
| 401 | `WorkspaceUnauthorizedError` | Missing, expired, not-yet-propagated, or invalid token for the workspace. | Reissue or refresh token; if just created, wait briefly and retry. |
| 403 | `WorkspaceForbiddenError` | Token does not grant access to the workspace URL, often a URL/environment mismatch. | Check `lep workspace url` and any `LEPTON_WORKSPACE_URL`; login again with the correct API URL. |
| 404 | `WorkspaceNotFoundError` | Workspace id not found or workspace not fully created yet. | Verify the id; wait for workspace provisioning if newly created. |

The exception object can contain workspace id, workspace URL, and a masked token hint. Keep it masked.

## Token expiry behavior

- `APIClient` reads `token_expires_at` from the persisted workspace record when present.
- The client warns once per process when the recorded token is expired or has fewer than ten days left.
- `lep workspace list` displays expiry as expired, less than one day, yellow under ten days, green at thirty days or more, or `-` when unavailable.
- Expiry lookup is available only for supported DGX Cloud Lepton workspaces. Missing expiry can also mean the token cannot be matched or is already unusable.

## URL and origin behavior

- If no URL is provided or stored, Lepton builds the default workspace API URL from the workspace id.
- For DGX Cloud Lepton URLs, the derived origin URL is the API URL; for classic/non-DGXC URLs, no origin URL may be required.
- A token issued for one Lepton environment can fail with 403 when used against another workspace API URL. Align the token issuer, workspace id, `--workspace-url`, and any `LEPTON_WORKSPACE_URL` override before retrying.
