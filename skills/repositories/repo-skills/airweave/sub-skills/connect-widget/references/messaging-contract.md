# Messaging contract

## Trust and origin rules

- The child sends messages only after it is embedded in an iframe. If it is not inside an iframe, parent messaging is skipped.
- The first `TOKEN_RESPONSE` or `TOKEN_ERROR` establishes the trusted parent origin.
- After that, every incoming message must match that origin.
- `CONNECT_READY` is the only initial message that may go out before origin is known, so the parent can reply with a token.
- `requestToken()` waits up to 10 seconds; timeout resolves to `null`.
- Ignore malformed data without a `type`.

## Child → parent

| Type | Payload | When sent | Notes |
| --- | --- | --- | --- |
| `CONNECT_READY` | none | once after mount | Parent should answer with a token or an error. |
| `REQUEST_TOKEN` | `requestId` | when the widget needs a token or retries | Parent must echo the same `requestId`. |
| `STATUS_CHANGE` | `status` | whenever session state changes | Useful for host-side telemetry or UI chrome. |
| `CONNECTION_CREATED` | `connectionId` | after successful connection creation or reauth success | Parent can store or route the new connection. |
| `CLOSE` | `reason` | when user cancels, succeeds, or hits a fatal error | Parent should remove the iframe or modal. |

## Parent → child

| Type | Payload | When sent | Notes |
| --- | --- | --- | --- |
| `TOKEN_RESPONSE` | `requestId`, `token`, optional `theme` | in response to `REQUEST_TOKEN` | The widget applies `theme` immediately, then validates the token. |
| `TOKEN_ERROR` | `requestId`, `error` | in response to `REQUEST_TOKEN` | Treated as a null response; the widget shows an error state. |
| `SET_THEME` | `theme` | anytime after mount | Updates the widget live. |
| `NAVIGATE` | `view` | anytime after mount | Valid views: `connections`, `sources`, `configure`, `folder-selection`. |

## Theme payload notes

- `ConnectTheme` can carry `mode`, `colors`, `fonts`, `labels`, and `options`.
- `theme.options.enableFolderSelection` switches the success flow to the folder-selection branch.
- `theme.options.showConnectionName` controls whether the connection name field appears.
- `theme.options.logoUrl` feeds the welcome or empty-state branding.
- `mode: "system"` resolves against the browser's color-scheme media query.

## Session status values

The child reports these status states through `STATUS_CHANGE`:

- `idle`
- `waiting_for_token`
- `validating`
- `valid` with session context
- `error` with a structured session error

Session error codes are `invalid_token`, `expired_token`, `network_error`, and `session_mismatch`.

## Failure handling

- If token validation fails with `401`, the widget maps it to invalid or expired token and can request one fresh token retry.
- If validation fails with `403`, the widget maps it to `session_mismatch` and does not retry automatically.
- If the parent stays silent, the request times out and the widget waits for a manual retry.
- If the parent sends a response from a different origin after trust is established, the widget ignores it.
