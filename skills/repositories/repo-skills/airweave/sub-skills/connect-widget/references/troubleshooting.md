# Connect widget troubleshooting

## Fast triage checklist

1. Confirm the widget is running inside an iframe. Top-level launches skip parent messaging.
2. Confirm the parent listens for `CONNECT_READY` and answers `REQUEST_TOKEN` with the same `requestId`.
3. Confirm the parent replies from the same origin that will handle later messages.
4. Confirm the session token is fresh and the session mode matches the action you want.
5. Confirm the OAuth popup can open and the redirect URL returns to the same origin.
6. Confirm the backend route in question belongs to the widget flow and not the dashboard or generic API surface.

If the problem is actually session creation, source-connection lifecycle, or backend response shape, route to [backend-api](../../backend-api/SKILL.md). If the problem is the host application's modal or launch flow, route to [frontend-dashboard](../../frontend-dashboard/SKILL.md).

## Handshake and origin problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Widget stays on loading | Parent never answered `REQUEST_TOKEN`, or it answered with the wrong `requestId`. | Make sure the host page receives `CONNECT_READY` and sends `TOKEN_RESPONSE` promptly. |
| Widget never talks to parent | It is not embedded in an iframe. | Mount it in a parent frame or host shell; top-level pages intentionally skip messaging. |
| Later parent messages are ignored | The widget locked to the first trusted origin. | Make sure the same window/origin that answered the token request sends later `SET_THEME` or `NAVIGATE` messages. |
| `STATUS_CHANGE` never appears | Token request timed out or token validation failed before the success state. | Check parent logging and re-send a fresh token. |

## Session and token problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Error screen says invalid token | Token is malformed or the parent never provided a usable session token. | Fetch a fresh session token and resend it. |
| Error screen says expired token | The signed session token expired before validation. | Request a new session and re-open the widget. |
| Error screen says session mismatch | The session ID in the token does not match the validation request. | Use the matching session token or create a new session. |
| Error screen says network error | Backend API unreachable or the API URL is wrong. | Verify the API base URL and backend availability. |
| Retry still fails once | The widget already retried its one automatic token refresh. | Have the parent fetch a brand-new token instead of replaying the old one. |

## OAuth popup and callback problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Popup blocked notice appears | Browser blocked the OAuth popup. | Use the manual open-link action or retry after allowing popups. |
| OAuth popup closes without success | User closed the popup, or the callback route did not return. | Reopen OAuth; the flow returns to idle when the popup disappears. |
| OAuth callback shows failure | The callback returned `status=error` or an error message. | Reopen the flow after fixing the provider-side issue. |
| Reauth never completes | The popup callback never posted back, or `verifyOAuth` failed. | Keep the claim token until verification succeeds; then retry the flow if needed. |
| A new connection remains pending-auth | The claim token was dropped too early or `verify-oauth` never ran. | Re-initiate OAuth and verify ownership before clearing the claim token. |

## Mode and navigation problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| No create button appears | Session mode is `manage` or `reauth`. | Use `all` or `connect` when creation is required. |
| Source list is empty even though the backend has integrations | `allowed_integrations` filters out the sources, or the org feature flags hide them. | Adjust the session scope or switch to a broader session. |
| `NAVIGATE` seems ignored | Wrong view name or no trusted origin yet. | Send one of `connections`, `sources`, `configure`, or `folder-selection` after trust is established. |

## Folder selection problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Start sync button stays disabled | No folder is selected. | Select at least one folder or root. |
| Back action leaves a stale connection | The cleanup delete failed silently. | Refresh the connection list and delete the new connection manually if needed. |
| Folder tree selection feels inconsistent | The tree toggles descendants, not just the clicked folder. | Treat the parent row as a subtree selection control. |

## Sync progress problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| No progress indicator appears | The connection is not syncing yet, or there is no active/pending job. | Wait for a running job, or trigger the sync first. |
| Progress shows stale counts | The SSE stream has not delivered a newer update yet. | Let `useSyncProgress` reconnect, or refresh the connection list after completion. |
| Progress says reconnecting forever | SSE reconnect is failing or the backend stream is unavailable. | Verify network access to the backend SSE endpoint and retry. |
| Completed count looks wrong | Deleted entities are excluded from the displayed total. | This is expected; the indicator shows inserted + updated + kept + skipped only. |

## When to escalate

- Escalate to [backend-api](../../backend-api/SKILL.md) when the backend session, OAuth verification, source-connection, or SSE endpoint is the problem.
- Escalate to [frontend-dashboard](../../frontend-dashboard/SKILL.md) when the host app cannot open, mount, or tear down the widget correctly.
- Escalate to the widget flow itself when the issue is limited to iframe messaging, token exchange, OAuth popup recovery, or sync-progress rendering.
