# Multi-Channel Measurement API

Use this reference when a Mycodo client needs the latest values from several
sensor channels in one REST request. This endpoint is useful for mobile clients,
external Dashboards, polling integrations, or any automation that would
otherwise issue one request per channel.

## Endpoint

```text
POST /api/measurements/multi
```

Although the method is `POST`, this endpoint is a read/query operation: it asks
InfluxDB for the latest value for each requested channel within a lookback
window. It does not write measurements or actuate hardware.

Required headers:

```text
Accept: application/vnd.mycodo.v1+json
Content-Type: application/json
X-API-KEY: <base64-key-from-user-settings>
```

Some examples for this feature use `Authorization: Bearer <key>`. Prefer
`X-API-KEY` unless the live instance proves Bearer support; the inspected
request loader accepts `X-API-KEY`, `Authorization: Basic <base64-api-key>`, and
`api_key=<base64-api-key>` query authentication.

## Request Schema

```json
{
  "channels": [
    {
      "unique_id": "sensor_unique_id",
      "unit": "C",
      "channel": 0,
      "measure": "temperature"
    }
  ],
  "past_seconds": 3600
}
```

Fields:

| Field | Required | Meaning |
|---|---:|---|
| `channels` | yes | Non-empty list of channel specifications. |
| `channels[].unique_id` | yes | Mycodo device unique ID, commonly an Input unique ID. |
| `channels[].unit` | yes | Unit ID used in Mycodo/InfluxDB, such as `C`, `%`, `hPa`, `ppm`, or a custom unit. |
| `channels[].channel` | yes | Channel number, typically zero-based. Must be `>= 0`. |
| `channels[].measure` | no | Descriptive measurement type such as `temperature`, `humidity`, or `pressure`; echoed in the response for client clarity. |
| `past_seconds` | no | Lookback window. Defaults to `3600`; must be `>= 1`. |

The API validates that the channels list exists, every channel spec is an
object, required fields are present, units are valid Mycodo unit IDs, channel
numbers are non-negative, and `past_seconds` is positive.

## Response Schema

```json
{
  "measurements": [
    {
      "unique_id": "sensor_unique_id",
      "unit": "C",
      "channel": 0,
      "measure": "temperature",
      "time": 1703894523.456,
      "value": 23.5
    }
  ]
}
```

Response notes:

- Output order matches request channel order.
- `measure` is echoed from the request and may be `null`/missing if omitted.
- If no value exists in the lookback window for a channel, that channel can
  return `time: null` and `value: null` instead of failing the whole request.
- The returned `time` is a numeric timestamp from the InfluxDB result path.

## Channel Planning Workflow

1. Discover candidate devices and units:
   - `GET /api/inputs/` for Input settings and Input channels.
   - `GET /api/settings/device_measurements` or
     `GET /api/settings/device_measurements/<unique_id>` for device measurement
     mappings.
   - `GET /api/choices/inputs/measurements` for UI-style choices.
   - `GET /api/settings/units` for valid unit IDs.
2. Identify each desired measurement's `unique_id`, `unit`, and `channel`.
3. Choose `past_seconds` based on the slowest sensor update interval plus a
   margin. A one-hour default is reasonable for manual testing, but production
   clients should use the smallest window that tolerates missed measurements.
4. Build a request with all channels needed for one client refresh cycle.
5. Treat `null` values as "no recent value found" and decide whether to show
   stale/unknown, retry later, or widen `past_seconds`.
6. Rate-limit polling. Batching reduces round trips but still queries InfluxDB.

## `curl` Example

```bash
curl -k -sS -X POST "https://mycodo.local/api/measurements/multi" \
  -H "Accept: application/vnd.mycodo.v1+json" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <base64-key-from-user-settings>" \
  --data '{
    "channels": [
      {"unique_id": "bme680_input_id", "unit": "C", "channel": 0, "measure": "temperature"},
      {"unique_id": "bme680_input_id", "unit": "%", "channel": 1, "measure": "humidity"},
      {"unique_id": "bme680_input_id", "unit": "hPa", "channel": 2, "measure": "pressure"}
    ],
    "past_seconds": 3600
  }'
```

Replace IDs, units, and channels with values discovered from the target Mycodo
instance. Do not assume a BME680/BME688 or Atlas Scientific device uses the same
channel order as another installation.

## Python Example

```python
import requests

api_key = "<base64-key-from-user-settings>"
url = "https://mycodo.local/api/measurements/multi"
headers = {
    "Accept": "application/vnd.mycodo.v1+json",
    "Content-Type": "application/json",
    "X-API-KEY": api_key,
}
payload = {
    "channels": [
        {"unique_id": "sensor_001", "unit": "C", "channel": 0, "measure": "temperature"},
        {"unique_id": "sensor_001", "unit": "%", "channel": 1, "measure": "humidity"},
    ],
    "past_seconds": 3600,
}

response = requests.post(url, headers=headers, json=payload, timeout=20, verify=False)
if response.status_code == 200:
    data = response.json()
    for item in data["measurements"]:
        print(item["measure"], item["value"], item["unit"], item["time"])
else:
    print(response.status_code, response.text)
    response.raise_for_status()
```

Use `verify=False` only for a trusted local/self-signed certificate. Keep TLS
verification enabled for production/public hosts.

## Using The Bundled Helper

The helper can send this endpoint without embedding a key in the command:

```bash
export MYCODO_API_KEY="<base64-key-from-user-settings>"
python scripts/mycodo_api_request.py \
  --host https://mycodo.local \
  --endpoint /api/measurements/multi \
  --method POST \
  --json '{
    "channels": [
      {"unique_id": "sensor_001", "unit": "C", "channel": 0, "measure": "temperature"},
      {"unique_id": "sensor_001", "unit": "%", "channel": 1, "measure": "humidity"}
    ],
    "past_seconds": 3600
  }' \
  --insecure
```

The helper prints the status, a subset of headers, and parsed JSON/text body. A
non-`2xx`/`3xx` response exits nonzero after printing the response.

## Use Cases

### Multi-Channel Environmental Sensor

For a device that stores temperature, humidity, pressure, and gas resistance in
separate channels, batch all channels in one request. Benefits are largest when
network latency is non-trivial because one HTTPS round trip replaces several.

### Multiple Sensors Dashboard

For an external Dashboard or mobile app, combine one representative latest value
from each device into a single refresh request. Keep the response order stable
by keeping channel list order stable.

### Health Monitor With Missing Values

A monitoring client can distinguish three states per channel:

- HTTP/request failure: no trustworthy batch result.
- Successful response with `value: null`: no recent InfluxDB value for that
  channel within `past_seconds`.
- Successful response with numeric value: fresh-enough channel reading.

Use that distinction to avoid incorrectly treating missing sensor data as zero.

## Error Handling

- `401`: wrong/missing auth; switch to `X-API-KEY`, check the base64 API key,
  and ensure `MYCODO_API_KEY` was exported if using the helper.
- `403`: authenticated user lacks `view_settings`; use a user with sufficient
  read permission or reduce the task.
- `406`: missing/wrong `Accept`; send `application/vnd.mycodo.v1+json`.
- `422`: request body missing, `channels` absent/not a list/empty, channel spec
  not an object, missing `unique_id`/`unit`/`channel`, invalid unit, channel `< 0`,
  or `past_seconds < 1`.
- `500`: Mycodo server exception or InfluxDB/data-layer problem. Do not broaden
  permissions or mutate services without diagnosis.

## Performance And Polling

If a client needs `N` channels and each HTTPS request has `L` milliseconds of
latency, batching saves roughly `(N - 1) * L` latency versus sequential one
channel requests. It does not eliminate per-channel InfluxDB query work, so very
large channel lists can still be expensive.

Recommended polling practices:

- Poll no faster than the underlying Input measurement intervals unless the user
  explicitly requests near-real-time behavior.
- Group channels by client screen or automation decision rather than querying
  every configured device each time.
- Back off on `429`, repeated `500`, or long response times.
- Cache static metadata such as units and channel mappings; refresh metadata
  when Mycodo settings change.

## Safety Boundaries

The multi-channel endpoint is read-only, but it can reveal sensor values,
locations, process states, or private environmental data. Treat responses as
sensitive. Stop and ask before changing InfluxDB configuration, web server TLS,
Mycodo services, hardware drivers, or installer state to make this endpoint work.
