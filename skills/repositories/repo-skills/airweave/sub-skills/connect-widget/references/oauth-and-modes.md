# OAuth and modes

## Session modes

| Mode | Widget behavior |
| --- | --- |
| `all` | Shows the connection list and allows the full create/manage/reauth flow. |
| `connect` | Starts from source selection and allows new connection creation. |
| `manage` | Focuses on the existing connection list; no create button. |
| `reauth` | Focuses on existing pending-auth connections and reauth recovery; no create button. |

`canConnect(mode)` is true only for `all` and `connect`.

## Connection creation flow

1. `SourceConfigView` loads source details and decides which auth fields to show.
2. Direct auth sends credentials inside `authentication.credentials`.
3. OAuth browser flow calls `useOAuthFlow`, creates the connection with a redirect URL to `/oauth-callback`, and waits for popup completion.
4. `claim_token` from the create response must be held until `verifyOAuth` succeeds.
5. If the popup is blocked, the UI offers `retryPopup` and a manual open-link path.
6. If the user closes the popup, the flow returns to idle and can call `onCancel`.

## OAuth callback recovery

- The callback page posts `OAUTH_COMPLETE` to `window.opener` using the same origin and closes itself after a short delay.
- `useOAuthFlow` closes the popup on success, verifies ownership if a claim token exists, and then calls `onSuccess(source_connection_id)`.
- If the callback reports error or the popup closes early, status becomes error or idle accordingly.
- Reauth uses the same popup/callback pattern as creation.

## Folder selection

- When `enableFolderSelection` is true, `SuccessScreen` routes to `folder-selection` after creation.
- `FolderTree` toggles a folder plus all descendants; the root row toggles everything.
- The start-sync button remains disabled until at least one folder is selected.
- Back removes the just-created connection best effort and returns to the source list.
- Folder IDs are kept client-side; this step does not persist them by itself.

## Sync progress

- `useSyncProgress` fetches jobs, retries briefly when jobs are not ready, subscribes to the active or pending job, and stores the last update.
- `onReconnecting` marks the subscription as reconnecting.
- `onComplete` marks completed or failed and removes the subscription after a short delay.
- `SyncProgressIndicator` counts inserted, updated, kept, and skipped entities; deleted is excluded from the total.
- `ConnectionItem` only shows progress for syncing connections.

## Reauth and reconnect

- Connections with `pending_auth` can show a reconnect action in the success shell.
- Reconnect uses the connection's auth URL, then listens for the same popup callback as the creation flow.
- Successful reauth should refresh the list and keep the latest connection selected.
- If the reauth flow returns a claim token, preserve it until ownership verification succeeds.

## Validation anchors

- `connect/tests/e2e/session.spec.ts` covers session modes and source filtering.
- `connect/tests/e2e/widget.spec.ts` and `connect/tests/e2e/sdk.spec.ts` cover iframe bootstrap and host integration.
- `connect/src/components/SyncProgressIndicator.test.tsx` covers rendered progress states.
- `connect/src/hooks/useSyncProgress.test.ts` covers SSE subscription state transitions.
