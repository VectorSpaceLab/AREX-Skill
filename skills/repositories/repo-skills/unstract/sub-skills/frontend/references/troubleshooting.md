# Frontend Troubleshooting

## Common Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The UI still points at an old backend | `window.RUNTIME_CONFIG` was not regenerated or the browser cached the old asset | Regenerate the runtime config and hard-refresh the browser |
| Vite cannot reach the backend in dev | `VITE_BACKEND_URL` is missing or wrong | Set the backend URL and restart the dev server |
| A route loads the wrong shell / page | The route tree in `Router.jsx` or `useMainAppRoutes.js` changed | Compare the route helper and the authenticated subtree |
| Build fails on an optional plugin import | The plugin is absent and the Vite optional-plugin shim is not doing its job | Check the optional import path and the plugin shim in `vite.config.js` |
| Socket.IO / websocket log streaming fails in dev | The dev proxy is not forwarding websocket upgrades | Check the `/api` proxy block in `vite.config.js` |

## Environment Pitfalls

- Use `VITE_*` env vars for this app. `REACT_APP_*` names are only a compatibility fallback in the runtime-config generator.
- The frontend expects Node.js / Bun versions that match the repo README. Older runtimes often fail in a way that looks like a package issue but is really a toolchain mismatch.
- `bun run build` is a better first smoke check than a browser session if the problem is clearly a compile / route / config issue.

## What To Check First

1. Confirm the runtime config file was regenerated.
2. Confirm `VITE_BACKEND_URL` and the relevant runtime env vars are set.
3. Confirm the route tree owns the page you are trying to reach.
4. Confirm the dev proxy is forwarding websocket upgrades if the problem is log streaming.
