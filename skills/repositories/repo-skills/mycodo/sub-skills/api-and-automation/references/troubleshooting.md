# API And Automation Troubleshooting

Use this guide when REST API calls, `DaemonControl`, Pyro, or `mycodo-client`
automation fails. Prefer diagnosis with read-only probes before retrying any
state-changing operation.

## First Safe Probes

1. Confirm the target host and scheme:
   ```bash
   curl -k -I "https://mycodo.local/api"
   ```
2. Confirm API media type and auth with a read-only endpoint:
   ```bash
   curl -k -sS "https://mycodo.local/api/daemon/" \
     -H "Accept: application/vnd.mycodo.v1+json" \
     -H "X-API-KEY: <base64-key-from-user-settings>"
   ```
3. If local on the Mycodo host, check the daemon:
   ```bash
   mycodo-client --checkdaemon
   ```
4. If using Python, retry with the bundled helper so status, selected headers,
   and body are visible:
   ```bash
   MYCODO_API_KEY="<base64-key-from-user-settings>" \
   python scripts/mycodo_api_request.py \
     --host https://mycodo.local \
     --endpoint /api/daemon/ \
     --method GET \
     --insecure
   ```

## REST Symptoms

| Symptom | Likely causes | Concrete recovery | Stop when |
|---|---|---|---|
| TLS certificate verification failure | Local Mycodo uses self-signed certificate; hostname mismatch; expired cert. | For trusted local hosts, use `curl -k`, `requests verify=False`, or helper `--insecure`. For production/public hosts, install or select a valid cert instead. | Do not weaken TLS for an untrusted or public host without user approval. |
| Plain HTTP fails or redirects unexpectedly | API expects HTTPS; reverse proxy mismatch. | Use `https://<host>/api/...`; inspect `/api` over HTTPS. | Stop before changing nginx/web server configuration. |
| `401 Invalid API Key` | Missing key; wrong base64 string; using Bearer when instance expects `X-API-KEY`; environment variable not set; query string `+` converted to space. | Prefer `X-API-KEY`. Re-copy key from user settings. If using query auth, URL-encode or replace spaces with `+`. Check `MYCODO_API_KEY`. | Stop if credentials are unknown, expired, or not authorized for the user. |
| `403 Insufficient Permissions` | API key belongs to a user without `view_settings` or `edit_controllers`. | Use a user role with the minimum necessary permission or reduce to permitted read-only endpoints. | Stop before privilege escalation; ask user for a suitable key. |
| `404 Not Found` | Wrong namespace/path; endpoint missing in installed version; reverse proxy prefix; trailing slash mismatch. | Visit `https://<host>/api`; try exact listed route including prefix `/api`. Check whether route needs a trailing slash, e.g. `/api/daemon/`. | Stop before assuming a route exists across versions. |
| `406` / content negotiation error | Missing or wrong `Accept` header. | Send `Accept: application/vnd.mycodo.v1+json`. | Stop if live API documents a different version and user has not approved version-specific adaptation. |
| `422 Unprocessable Entity` | Invalid path/body parameter: missing `activate`, invalid unit, negative channel, bad timestamp, empty channels list, `past_seconds < 1`, non-numeric value. | Compare request against the endpoint schema at `/api`; validate units/channels via `/api/settings/...` or `/api/choices/...`; fix payload. | Stop before guessing units, channels, or Output/PID IDs. |
| `429 Too Many Requests` | Polling too fast or proxy rate limiting. | Back off, reduce polling frequency, batch with `/api/measurements/multi`, cache metadata. | Stop before increasing load on a struggling Mycodo host. |
| `460` with JSON message | Daemon operation failed after API validation, often wrong Output/Input/controller ID/channel or daemon-side error. | Read message, verify target IDs with read-only endpoints, check daemon status. Retry only after correcting the cause. | Stop before repeating hardware-changing commands. |
| `500 Internal Server Error` | Server exception, daemon unavailable, database/InfluxDB error, endpoint bug. | Check response body, logs if authorized, daemon status, and InfluxDB/service health. Retry read-only requests after transient recovery. | Stop before restarting services, changing databases, or rerunning installers. |
| JSON parse error | Endpoint returned HTML error page, image/binary, empty body, or wrong `Accept`. | Print response text and `Content-Type`; confirm endpoint family. Use camera endpoints as binary/image-sensitive. | Stop before feeding non-JSON to downstream automation. |

## Authentication Checklist

- Use the base64 API key as shown in the web UI user settings.
- Preferred header: `X-API-KEY: <base64-key>`.
- Alternate header: `Authorization: Basic <base64-key>`.
- Avoid `api_key=<base64-key>` query auth unless unavoidable.
- Do not rely on `Authorization: Bearer <key>` unless the live deployment proves
  support.
- Keep keys out of logs and shell history where possible. Prefer environment
  variables or secret managers.

## Endpoint And Payload Checklist

Before mutating anything:

1. Read endpoint documentation from the live `/api` page.
2. Confirm the method (`GET` vs `POST`) and body schema.
3. Discover IDs through read-only endpoints:
   - `/api/settings/inputs`, `/api/inputs/`, `/api/choices/inputs/measurements`
   - `/api/settings/outputs`, `/api/outputs/`, `/api/choices/outputs/devices`
   - `/api/settings/pids`, `/api/pids/`, `/api/choices/pids/measurements`
   - `/api/settings/triggers` for Trigger settings
4. Confirm zero-based channels where relevant.
5. Confirm units exist with `/api/settings/units`.
6. Confirm permission boundary: read endpoints usually need `view_settings`;
   Output/controller/daemon mutations usually need `edit_controllers`.

## Output/Controller/PID Safety Failures

Symptoms:

- Output command returns success but hardware does not change.
- Output command returns `460`.
- Controller activation succeeds but expected Conditional/Trigger/Function does
  not run.
- PID setpoint/gain command does not have expected effect.

Likely causes:

- Wrong `unique_id`, stale ID, or wrong channel.
- Output type mismatch (`state`, `duration`, `duty_cycle`, or `volume`).
- Daemon stale settings; controller needs refresh/restart.
- Hardware backend unavailable or not verified on this host.
- Insufficient user permission or local daemon failure.

Recovery:

1. Stop repeating the actuation command.
2. Query current settings/state with `/api/outputs/`, `/api/controllers/<id>`, or
   direct `DaemonControl` read methods.
3. Confirm channel and Output type in the web UI or settings endpoints.
4. Check daemon status with `/api/daemon/` or `mycodo-client --checkdaemon`.
5. Only after the user approves, refresh/restart the specific controller or use
   `DaemonControl` to reload settings.

Stop before:

- Physically rewiring devices.
- Changing GPIO/I2C/UART/1-Wire/Bluetooth/camera settings.
- Restarting services or editing system files.
- Re-running installers or dependency installation routes.

## Multi-Channel Measurement Problems

| Symptom | Likely causes | Recovery |
|---|---|---|
| `422` invalid unit | Unit ID does not match Mycodo units/custom units. | Query `/api/settings/units` and use the unit ID exactly. |
| `422` invalid channel | Channel missing, non-integer, or `< 0`. | Use zero-based channel integers from Input/device measurement settings. |
| Values are `null` | No InfluxDB point found within `past_seconds`; wrong unit/channel/device; sensor not measuring. | Widen `past_seconds`, verify single-channel `/api/measurements/last/...`, check Input state and measurement interval. |
| Batch succeeds but slow | Too many channels or InfluxDB load. | Split by client screen, reduce frequency, cache metadata, avoid querying unused channels. |
| Some channels missing while others work | Per-channel validation or data availability differences. | Keep channel order stable and handle per-item nulls; do not treat missing as zero. |

Stop before changing InfluxDB retention, service configuration, or sensor drivers
without explicit user approval.

## Pyro / DaemonControl Problems

| Symptom | Likely causes | Recovery | Stop when |
|---|---|---|---|
| `ModuleNotFoundError: mycodo` | Python is not the Mycodo installed environment. | Run with the Mycodo environment Python, commonly under `/opt/Mycodo/env`, or activate the user's configured environment. | Stop before modifying environments globally. |
| `Pyro5 TimeoutError` | Daemon busy, method blocked on hardware, too-short timeout. | Increase `pyro_timeout` for read-only probes; check daemon load; avoid repeated hardware calls. | Stop before restarting daemon or changing hardware services. |
| `Pyro5 CommunicationError` | Daemon/Pyro server not reachable; wrong URI. | Check `DaemonControl().check_daemon()`, `mycodo-client --checkdaemon`, configured URI. | Stop before exposing Pyro over network. |
| `Failed to locate Pyro5 Nameserver` | URI/startup mismatch. | Confirm daemon is running and local Pyro URI is correct. | Stop before editing daemon startup. |
| Method returns tuple with failure | Daemon method rejected operation or encountered controller error. | Inspect returned message, verify IDs/channels/settings, then retry only corrected command. | Stop before repeating actuation blindly. |

## `mycodo-client` Problems

- Command not found: use the Mycodo installed environment/path or ask the user
  where Mycodo is installed. Do not install/upgrade packages just to find it.
- Permission denied: run as the appropriate local Mycodo/operator user according
  to the installation. Do not escalate with `sudo` unless the user authorizes it.
- `--output_state`, `--outputoff`, `--outputon`, or `--output_currently_on`
  errors about channel: include `--output_channel <channel>`.
- PID commands behave unexpectedly: prefer direct `DaemonControl` methods for
  automation and verify the target PID state through read-only checks.
- `--terminate` would stop the daemon: require explicit approval.

## Network And Reverse Proxy Issues

Symptoms:

- API works on localhost but not remotely.
- Browser can show web UI but script gets 401/404/502.
- TLS works with `-k` but not with verification.

Recovery:

1. Confirm the URL path includes `/api` and the same hostname used by the web UI.
2. Check whether a reverse proxy changes path prefixes or strips auth headers.
3. Keep `X-API-KEY` header intact through the proxy.
4. Use a proper certificate for remote/public clients.
5. Avoid disabling certificate verification outside trusted local networks.

Stop before editing nginx, firewall, DNS, certificates, or Docker compose files
unless the user explicitly asks for system/network changes.

## Data Privacy And Logging

- API responses may include user settings, camera imagery, logs, sensor values,
  and environment/process state.
- Backup/export endpoints can contain secrets and historical data.
- Logs may contain tokens, webhook URLs, email addresses, or operational events.
- Redact API keys before sharing commands or responses.

## Verification Limits To Keep Honest

The guidance here was verified by CPU/source inspection and distilled runtime
facts. Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera behavior,
systemd/nginx/InfluxDB operations, Docker deployment, backup/restore, and full
installer execution were not run. Treat failures in those surfaces as live
operations requiring user consent, maintenance windows, and rollback planning.
