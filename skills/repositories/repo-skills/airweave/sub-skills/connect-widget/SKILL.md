---
name: connect-widget
description: "Operates the embeddable Connect widget iframe, client-side session
  UX, parent-child postMessage, OAuth popup recovery, theme updates, connection
  creation, folder selection, and sync progress handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Connect Widget

Use this sub-skill when an Airweave task touches the embeddable Connect widget itself: iframe mount and shutdown, session token request and validation, parent-child messaging, live theme updates, OAuth popup recovery, connection creation, folder selection, or sync progress rendering.

Do not use this sub-skill for backend endpoint lifecycle, dashboard UI, MCP transport, or Monke orchestration. For route and schema details, cross-link to [backend-api](../backend-api/SKILL.md). For dashboard-hosted launch flows around the widget, cross-link to [frontend-dashboard](../frontend-dashboard/SKILL.md).

## Route to the right reference

- Read [references/widget-overview.md](references/widget-overview.md) for the widget lifecycle, state machine, and module responsibility map.
- Read [references/messaging-contract.md](references/messaging-contract.md) for `CONNECT_READY`, token exchange, trusted-origin behavior, `NAVIGATE`, `SET_THEME`, `STATUS_CHANGE`, `CONNECTION_CREATED`, and `CLOSE`.
- Read [references/oauth-and-modes.md](references/oauth-and-modes.md) for session modes, source creation, OAuth popup and callback recovery, folder selection, reauth handling, and sync progress behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) when the widget stalls, the parent origin is rejected, tokens time out, OAuth popups are blocked, callbacks fail, or sync state stops updating.

## Operating rules

1. Treat the widget as a child iframe app. It should announce readiness, wait for a parent session token, validate that token, and then switch into a valid or error state.
2. Lock the parent origin after the first token response or token error. Later messages from a different origin are unsafe and should be ignored.
3. Apply theme updates immediately. Initial theme can come from the iframe URL, token response, or later `SET_THEME` messages, and the widget should keep rendering with the latest theme.
4. Honor session mode. `all` and `connect` can launch new connections; `manage` and `reauth` focus on existing connections and reauth flows.
5. Preserve OAuth claim-token recovery. Do not discard the claim token until verification succeeds, and surface popup-blocked or callback-loss cases as recoverable errors.
6. Keep folder selection client-side until completion. If the user backs out of a freshly created connection, clean up the connection instead of leaving it stranded.
7. Treat SSE sync progress as authoritative while a sync is active. Handle reconnecting, terminal success, and terminal failure separately from the connection list summary.

## Quick decision map

| User intent | Start here | Notes |
| --- | --- | --- |
| "How does the iframe handshake work?" | `messaging-contract.md` | Covers `CONNECT_READY` → token exchange → status updates. |
| "Why did OAuth fail or reopen?" | `oauth-and-modes.md` | Covers popup-blocked recovery, callback posting, and claim-token verification. |
| "How does folder selection behave?" | `oauth-and-modes.md` | Covers the selection step and back-out cleanup. |
| "Why is sync progress missing or stale?" | `oauth-and-modes.md` and `troubleshooting.md` | Covers SSE subscription, reconnecting, and terminal progress states. |
| "Why does the widget close or show an error?" | `troubleshooting.md` | Covers origin mismatch, timeouts, session mismatch, and unsupported launch states. |

## Validation anchors

Later verification should prioritize the native widget tests and unit anchors:

- `connect/tests/e2e/session.spec.ts`
- `connect/tests/e2e/widget.spec.ts`
- `connect/tests/e2e/sdk.spec.ts`
- `connect/src/components/SyncProgressIndicator.test.tsx`
- `connect/src/hooks/useSyncProgress.test.ts`
