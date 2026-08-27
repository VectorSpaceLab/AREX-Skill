# Widget overview

## What this reference covers

This reference maps the Connect widget lifecycle, the modules that own each stage, and the client-side behaviors that future tasks should preserve.

## Architecture at a glance

| Responsibility | Primary module(s) | Notes |
| --- | --- | --- |
| iframe mount and initial theme | `SessionProvider`, `ThemeProvider`, `LoadingScreen` | `SessionProvider` reads the `theme` query param, wraps the widget in theme context, and keeps the loading state styled before validation completes. |
| iframe-parent handshake | `useParentMessaging` | Sends `CONNECT_READY`, waits for a token, captures the trusted parent origin, and forwards status, connection, navigation, theme, and close signals. |
| session validation | `apiClient.validateSession`, `SessionProvider` | Validates the signed session token and maps failures to session error states. |
| connection creation and OAuth | `SuccessScreen`, `SourceConfigView`, `useOAuthFlow`, `oauth-callback` | Handles direct auth, browser OAuth, BYOC, claim-token verification, and popup recovery. |
| folder selection | `SuccessScreen`, `FolderSelectionView`, `FolderTree` | Optional branch after connection creation when folder selection is enabled. |
| live sync tracking | `useSyncProgress`, `SyncProgressIndicator`, `ConnectionItem` | Subscribes to SSE progress and reflects reconnecting, completed, and failed states. |
| error and retry UX | `ErrorScreen`, `SessionProvider`, `useParentMessaging` | Maps token problems to retry/close affordances and keeps the handshake visible to the parent. |

## Lifecycle

1. Mount: `SessionProvider` computes an initial theme from the iframe URL and enters the loading state.
2. Ready signal: `useParentMessaging` sends `CONNECT_READY` once the iframe is running in a parent context.
3. Token request: the widget asks the parent for a token and waits up to 10 seconds for a matching reply.
4. Validation: the token is applied to the API client and validated to get a `ConnectSessionContext`.
5. Success shell: `SuccessScreen` chooses the default view from the session mode and renders either the connection list, source configuration, or folder selection.
6. Connection flow: `SourceConfigView` creates the connection; OAuth flows route through `useOAuthFlow`, and successful creation emits `CONNECTION_CREATED`.
7. Sync tracking: `useSyncProgress` attaches to the newest active job and drives `SyncProgressIndicator`.
8. Shutdown: `requestClose` tells the parent why the widget wants to close; the parent should tear down the iframe.

## Important behavior notes

- Parent theme updates can happen before or after validation.
- `manage` and `reauth` sessions still need the connection list, but they should not show the create-connection button.
- `FolderSelectionView` keeps selected folder IDs locally; it does not persist them itself.
- `ConnectionItem` only shows progress when the connection is currently syncing.
- `SuccessScreen` invalidates the connection list after creation, deletion, reconnect success, or folder-selection completion.
- The widget is intended to run embedded. If it is opened as a top-level page, parent messaging is skipped.

## Validation anchors

- `connect/tests/e2e/widget.spec.ts` checks iframe load and handshake.
- `connect/tests/e2e/sdk.spec.ts` checks the bootstrap path used by host integrations.
- `connect/tests/e2e/session.spec.ts` checks session creation, mode restrictions, and source filtering.
- `connect/src/components/SyncProgressIndicator.test.tsx` checks sync-progress rendering states.
- `connect/src/hooks/useSyncProgress.test.ts` covers subscription state transitions.
