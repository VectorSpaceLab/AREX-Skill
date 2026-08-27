# Mycodo REST API Runtime Guide

Use this reference to build Mycodo HTTPS REST calls without reopening repository
material. The live Mycodo instance exposes generated endpoint documentation at
`https://<mycodo-host>/api`; use that page to confirm the exact installed API
shape before sending mutating requests.

## Base Contract

- Base prefix: `/api`.
- Transport: HTTPS. Plain HTTP API calls are expected to fail.
- Version/media type: send `Accept: application/vnd.mycodo.v1+json`.
- JSON request bodies: send `Content-Type: application/json` when a body is
  present.
- API keys are generated in the web UI user settings page. The visible key is a
  base64-encoded representation of bytes stored for the user. Treat it as a
  password.
- Successful responses are normally `2xx`; client/auth/payload failures are
  `4xx`; server failures are `5xx`; daemon command failures can return `460`.

## Authentication Forms

Prefer this header for automation:

```text
X-API-KEY: <base64-key-from-user-settings>
```

The request loader also accepts these forms:

```text
Authorization: Basic <base64-key-from-user-settings>
```

```text
https://<mycodo-host>/api/...?...&api_key=<base64-key-from-user-settings>
```

Avoid query-string API keys unless there is no better option because URLs are
commonly logged by proxies, terminals, and browser history.

Compatibility note: some multi-channel examples in circulation use
`Authorization: Bearer <key>`. The inspected Mycodo request loader authenticates
API key query strings, `Authorization: Basic ...`, and `X-API-KEY`; it does not
parse Bearer tokens. If a Bearer example returns `401`, retry with `X-API-KEY`.

## `curl` Patterns

Read-only daemon status, trusting a local self-signed certificate:

```bash
curl -k -sS "https://mycodo.local/api/daemon/" \
  -H "Accept: application/vnd.mycodo.v1+json" \
  -H "X-API-KEY: <base64-key-from-user-settings>"
```

Read all Input settings:

```bash
curl -k -sS "https://mycodo.local/api/inputs/" \
  -H "Accept: application/vnd.mycodo.v1+json" \
  -H "X-API-KEY: <base64-key-from-user-settings>"
```

Query the most recent InfluxDB-backed measurement for one channel:

```bash
curl -k -sS \
  "https://mycodo.local/api/measurements/last/<input_id>/C/0/3600" \
  -H "Accept: application/vnd.mycodo.v1+json" \
  -H "X-API-KEY: <base64-key-from-user-settings>"
```

For mutating requests, require the user to supply the endpoint, JSON body, and
explicit authorization. Example shape only:

```bash
curl -k -sS -X POST "https://mycodo.local/api/<user-confirmed-endpoint>" \
  -H "Accept: application/vnd.mycodo.v1+json" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <base64-key-from-user-settings>" \
  --data '<user-confirmed-json-body>'
```

## Python `requests` Pattern

```python
import requests

api_key = "<base64-key-from-user-settings>"
url = "https://mycodo.local/api/settings/outputs"
headers = {
    "Accept": "application/vnd.mycodo.v1+json",
    "X-API-KEY": api_key,
}
response = requests.get(url, headers=headers, timeout=20, verify=False)
print(response.status_code)
try:
    print(response.json())
except ValueError:
    print(response.text)
response.raise_for_status()
```

Use `verify=False` only for a trusted local/self-signed Mycodo host. For a public
or production deployment, install/use a valid certificate and keep verification
enabled.

## Endpoint Family Map

The following families were distilled from the API registration and route
surface. Use `/api` on the live instance for field-level schemas and installed
version differences.

| Family | Main routes | Typical use | Mutation risk |
|---|---|---|---|
| Choices | `GET /api/choices/controllers`, `/inputs/measurements`, `/outputs/devices`, `/outputs/measurements`, `/pids/measurements` | Discover IDs and valid selection lists for Inputs, Outputs, PID, controllers, units, and measurements. | Read-only. |
| Controllers | `GET /api/controllers/<unique_id>`, `POST /api/controllers/<unique_id>` | Check or activate/deactivate a controller. Applies to controller IDs such as Input, PID, Conditional, Trigger, or Function where supported by the daemon. | `POST` changes controller state. |
| Daemon | `GET /api/daemon/`, `POST /api/daemon/terminate` | Check daemon status, RAM, Python virtual environment; terminate daemon. | Termination is disruptive. |
| Dependency | `GET /api/dependency/install/device/<device_name>` | Install a dependency for a device. | Despite `GET`, this can mutate system/package state; stop for authorization. |
| Export/import | `GET /api/export_import/export_influxdb`, `GET /api/export_import/export_settings` | Export InfluxDB or settings backups. | Exports data; protect secrets and large files. |
| Functions | `GET /api/functions/`, `GET /api/functions/<unique_id>` | Inspect Function settings. Function Action execution is normally via DaemonControl or `mycodo-client`. | Read-only in listed REST routes. |
| Inputs | `GET /api/inputs/`, `GET /api/inputs/<unique_id>`, `POST /api/inputs/<unique_id>/force-measurement` | Inspect Input settings/channels/device measurements; force an Input measurement. | Force measurement can touch hardware. |
| Logs | `GET /api/logs/tail/<log_type>/<last_lines>` | Tail server/daemon logs exposed by the API. | Read-only but may expose secrets. |
| Measurements | `GET /api/measurements/last/...`, `/past/...`, `/historical/...`; `POST /api/measurements/multi`; `POST /api/measurements/create/...` | Read InfluxDB measurements, batch latest readings, or create a measurement value. | `create` writes data; `multi` is read-only despite `POST`. |
| Notes | `POST /api/notes/create` | Create a note. | Writes user-visible record. |
| Outputs | `GET /api/outputs/`, `GET /api/outputs/<unique_id>`, `POST /api/outputs/<unique_id>` | Inspect Output settings/channel states or change Output state, duration, PWM duty cycle, or volume. | Can actuate hardware. |
| PID | `GET /api/pids/`, `GET /api/pids/<unique_id>` | Inspect PID settings. PID pause/resume/set is via DaemonControl or `mycodo-client`. | Listed REST routes are read-only. |
| Settings | `GET /api/settings/{device_measurements,inputs,measurements,outputs,pids,triggers,units,users}` and `/<unique_id>` variants | Inspect SQL-backed settings. | Read-only, but may expose user/config data. |
| Camera | `GET /api/camera/capture_image/<unique_id>`, `/last_image/<unique_id>/<img_type>` | Capture or retrieve camera imagery. | Capturing can touch camera hardware and privacy-sensitive data. |
| Widgets/Dashboards | No dedicated REST namespace was present in the inspected API surface. | Use web UI for layout; local daemon has Widget helper methods for specific operations. | Treat UI/system changes as mutating. |

## Common Payloads

### Output Modulation

`POST /api/outputs/<output_id>` accepts a JSON body with:

- `channel` (required): output channel number, typically zero-based.
- `state` (optional bool): non-PWM on/off.
- `duration` (optional seconds): keep a non-PWM Output on for a duration.
- `duty_cycle` (optional 0-100): set PWM Output duty cycle.
- `volume` (optional non-negative float): send a volume amount.

Do not send this request unless the user confirms the Output ID, channel, and
physical consequence. If `state` plus `duration` are supplied, the daemon uses a
seconds-style output command. If `duty_cycle` is supplied, the daemon uses PWM.
If `volume` is supplied, the daemon uses volume output.

### Controller Activation

`POST /api/controllers/<controller_id>` expects:

```json
{"activate": true}
```

or:

```json
{"activate": false}
```

Confirm the controller ID and type before use. A wrong ID may fail with `460`,
`422`, or `500`, or affect an unintended controller if IDs were mixed up.

### Input Force Measurement

`POST /api/inputs/<input_id>/force-measurement` triggers the Input to acquire
measurements. This can touch hardware buses or sensors, so confirm the target
Input and acceptable timing before using it.

### Measurement Reads And Writes

- `GET /api/measurements/last/<unique_id>/<unit>/<channel>/<past_seconds>`
  returns the latest point in the lookback window as `{time, value}`.
- `GET /api/measurements/past/<unique_id>/<unit>/<channel>/<past_seconds>`
  returns a list of points in the lookback window.
- `GET /api/measurements/historical/<unique_id>/<unit>/<channel>/<epoch_start>/<epoch_end>`
  returns points between epoch bounds; set a bound to `0` for none.
- `POST /api/measurements/create/<unique_id>/<unit>/<channel>/<value>` writes a
  value, optionally with JSON `timestamp` formatted like
  `%Y-%m-%dT%H:%M:%S.%fZ`. Confirm unit and data ownership before writing.

## Status-Code Handling

- `200`: parse the body; still inspect message fields for daemon command result.
- `401`: missing/invalid API key, wrong auth header, wrong base64 string, or
  using Bearer on a deployment that expects `X-API-KEY`/Basic/query auth.
- `403`: authenticated user lacks permission such as `view_settings` or
  `edit_controllers`.
- `404`: wrong namespace/path, missing trailing slash on some routes, disabled
  API, reverse proxy mismatch, or installed version lacks the endpoint.
- `406` or content negotiation failure: missing/wrong `Accept` header. Use
  `application/vnd.mycodo.v1+json`.
- `422`: payload/path parameter validation failed, invalid unit ID, invalid
  channel, invalid timestamp, missing `activate`, empty channels list, or
  `past_seconds < 1`.
- `429`: too many requests; back off and avoid tight polling loops.
- `460`: Mycodo daemon operation reported failure. Read the JSON `message`, then
  check daemon health and target IDs.
- `500`: Mycodo server exception, daemon/InfluxDB/database problem, or endpoint
  bug. Do not retry destructive calls blindly.

## Endpoint Selection Heuristics

- Need IDs first? Start with `/api/choices/...` or `/api/settings/...`.
- Need current Output state? Use `GET /api/outputs/` or
  `GET /api/outputs/<output_id>`; it includes channel state data.
- Need one latest measurement? Use `/api/measurements/last/...`.
- Need several latest measurements? Use `/api/measurements/multi` from
  [multi-channel-api.md](multi-channel-api.md).
- Need PID values/setpoints or Function Action execution from Python? Use
  [daemon-client.md](daemon-client.md) rather than inventing undocumented REST
  paths.
- Need backup/export? Prefer web UI or a confirmed export route and treat output
  files as sensitive.

## Security Practices

- Keep API keys out of shell history where possible: prefer `MYCODO_API_KEY` or
  a secret manager over inline command arguments.
- Do not paste API keys into prompts, public logs, issue trackers, or generated
  skill files.
- Use role-scoped users where possible. Many read endpoints require
  `view_settings`; actuation endpoints commonly require `edit_controllers`.
- Never probe destructive endpoints just to discover behavior. Use `/api` docs,
  read-only endpoints, and user-confirmed IDs first.
- Rate-limit polling clients. Sensor dashboards and mobile apps should avoid
  short polling intervals that overload the web UI, daemon, or InfluxDB.
