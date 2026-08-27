# Server/API Troubleshooting

## Server Not Reachable

Symptoms:

- Browser or client cannot connect to `http://127.0.0.1:8188`.
- `Connection refused` from scripts.
- Websocket connect fails immediately.

Checks and fixes:

- Confirm the process is still running and startup completed.
- Confirm `--listen` and `--port`; default is `127.0.0.1:8188`.
- If connecting from another machine, do not use `127.0.0.1`; bind ComfyUI to a reachable interface and use that host from the client.
- If `--tls-keyfile` and `--tls-certfile` are used, clients must use `https://` and `wss://`.
- Temporarily start with `--disable-all-custom-nodes --disable-api-nodes` to isolate custom/API node startup failures from server problems.
- Backend/import failures during startup can prevent the HTTP server from coming up. Simplify backend flags and route model/backend diagnosis to `../../models-config/`.

## CORS or Browser Requests Fail

Symptoms:

- Browser integration gets CORS errors.
- ComfyUI logs host/origin mismatch warnings and returns `403`.
- Non-browser scripts work, but browser `fetch` does not.

Checks and fixes:

- For browser integrations, launch with `--enable-cors-header https://your-ui-origin.example` rather than `*` where possible.
- Do not expose `--enable-cors-header *` on untrusted networks without an external auth/security boundary.
- Default origin-only middleware is designed to prevent cross-site browser pages from posting workflows to a loopback ComfyUI server.
- For local scripts using Python HTTP clients, CORS is irrelevant; check URL, port, and TLS instead.

## TLS Misconfiguration

Symptoms:

- Server starts but clients fail certificate or protocol negotiation.
- `http://` works only when TLS flags are absent; `https://` needed when TLS is enabled.

Checks and fixes:

- Provide both `--tls-keyfile` and `--tls-certfile`.
- Use `https://host:port` for REST and `wss://host:port/ws?...` for websocket clients.
- For production, prefer a reverse proxy for certificate renewal, authentication, request limits, and audit logs.

## `POST /prompt` Returns `no_prompt` or Validation Errors

Symptoms:

- `400` with `error.type` of `no_prompt`.
- `400` with node validation errors.
- Server accepts JSON but rejects node graph.

Checks and fixes:

- Body must be an object with top-level `prompt`.
- `prompt` must be API workflow JSON exported with `File -> Export (API)`, not normal UI workflow JSON.
- Each node must have `class_type` and `inputs`.
- Node references should be `['node_id', output_index]` in JSON form.
- Validate graph semantics with `../../workflow-execution/` before posting.
- If using `prompt_id`, it must be a canonical lowercase hyphenated UUID. Omit `prompt_id` to let the server mint one.

## Websocket Progress Never Completes

Symptoms:

- Client receives messages but never exits.
- Binary frames cause JSON decoding errors.
- Completion for another prompt is mistaken for target completion.

Checks and fixes:

- Connect with the same `client_id` used in the `/prompt` body.
- Use the `prompt_id` returned by `/prompt`; do not assume the client id is the prompt id.
- Ignore non-text websocket frames unless intentionally processing previews or `SaveImageWebsocket` output.
- Completion is `type == 'executing'`, matching `prompt_id`, and `data.node is null`.
- Add a timeout and fall back to `GET /history/{prompt_id}` and `GET /queue`.

## `/history/{prompt_id}` Is Empty

Symptoms:

- Response is `{}`.
- Download step has no outputs.

Likely causes:

- Prompt is still queued or executing.
- Wrong `prompt_id` was used.
- Prompt failed before producing output nodes.
- History was cleared with `POST /history`.
- Server restarted.
- Workflow uses `SaveImageWebsocket` or non-file outputs instead of `SaveImage`.

Checks and fixes:

- Check `GET /queue` for running/pending prompt ids.
- Check `GET /api/jobs/{prompt_id}` where available.
- If websocket completed, inspect the full history entry for `status`, `outputs`, and node errors.
- Ensure the graph contains output nodes that write files when you expect `/view` downloads.

## `/view` Returns `400`, `403`, or `404`

Symptoms:

- Output exists in history but download fails.
- File path attempts are rejected.

Checks and fixes:

- Use exactly the `filename`, `subfolder`, and `type` values from history output items.
- Do not pass absolute paths or traversal segments; the server rejects these by design.
- If the file item uses an asset hash such as `blake3:<hash>`, pass it as `filename` and let the server resolve it.
- Confirm output history has not been deleted and the underlying file still exists.

## API Nodes Need Credentials

Symptoms:

- Hosted-provider/API nodes fail authentication.
- Workflow works in one session but not in automation.

Checks and fixes:

- Put the Comfy API key in `extra_data.api_key_comfy_org` in the `/prompt` request.
- Source the value from an environment variable or secret store.
- Do not commit keys in workflow JSON, examples, shell history, logs, or bundled scripts.
- Confirm the server was not started with `--disable-api-nodes`.
- If running offline or in a restricted deployment, use `--disable-api-nodes` intentionally and avoid workflows requiring hosted providers.

## User Data or Settings Behave Unexpectedly

Symptoms:

- `/settings` or `/userdata` differs between clients.
- File listing is empty even though files exist.
- User endpoints reject requests.

Checks and fixes:

- Check whether server started with `--multi-user`.
- Use `/users` to understand whether storage is multi-user server storage or default migrated storage.
- Use `/v2/userdata?path=...` for structured listings.
- Avoid path traversal and invalid characters; user-data routes validate paths and may return `400`, `403`, or `404`.
- If `--user-directory` or `--base-directory` was changed, confirm the intended user directory is being used.

## Assets Routes Return `503`

Symptoms:

- `/api/assets` returns service disabled.
- Asset hash lookup fails even though normal `/view` works.

Checks and fixes:

- Start with `--enable-assets` to enable assets routes, database synchronization, and background scanning.
- Confirm database dependencies initialized successfully.
- Treat the assets API as feature-gated; fallback to history output items plus `/view` for simple image downloads.

## Manager or Custom Node Endpoints Missing

Symptoms:

- Manager UI/endpoints unavailable.
- Custom node extensions fail to load or route behavior changes.

Checks and fixes:

- `--enable-manager` requires the manager package and its requirements to be installed.
- `--disable-manager-ui` disables manager UI/endpoints while preserving some background behavior.
- `--disable-all-custom-nodes` skips custom nodes; `--whitelist-custom-nodes` selectively re-enables named folders.
- Deprecated frontend extension paths can produce warnings; update the custom node extension or contact its maintainer.

## Safe Debugging Sequence

1. Start local-only: `python main.py --listen 127.0.0.1 --port 8188 --disable-all-custom-nodes --disable-api-nodes`.
2. Check `GET /system_stats` or `GET /prompt`.
3. Queue a known API-exported workflow with the bundled HTTP script using `--dry-run` first.
4. Re-enable required custom nodes or API nodes one at a time.
5. Add CORS/TLS/LAN exposure only after local automation works.
