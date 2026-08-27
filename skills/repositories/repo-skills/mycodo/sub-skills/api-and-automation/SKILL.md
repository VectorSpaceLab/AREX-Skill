---
name: api-and-automation
description: "Use Mycodo REST API authentication, versioned endpoints, Pyro
  DaemonControl, mycodo-client, and multi-channel automation safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Mycodo API And Automation

Use this sub-skill when the task involves Mycodo automation through HTTPS REST
endpoints, local Pyro daemon calls, the `mycodo-client` command line, or
multi-channel measurement queries. This skill is self-contained; do not reopen
repository docs, examples, or tests to use it at runtime.

## What This Sub-skill Owns

- API key authentication, HTTPS, self-signed certificate handling, and API media
  type/version selection.
- Selecting among REST API endpoints, local `DaemonControl`, and local
  `mycodo-client` automation.
- Endpoint families for Inputs, Outputs, Functions, Actions, Widgets,
  Dashboards, PID, Conditional, Trigger, measurements, InfluxDB-backed reads,
  daemon status, settings, choices, logs, camera images, and backup exports.
- Safe request patterns for `curl`, Python `requests`, and reusable scripts.
- Multi-channel measurement API planning and request/response handling.
- Error handling for API 4xx/5xx, Mycodo-specific `460` operation failures,
  TLS errors, Pyro timeouts, credential problems, and unsafe system mutations.

## Start Here: Choose The Automation Surface

1. **Use REST API** when the caller has a Mycodo web UI host, an API key, and
   needs remote or language-neutral automation over HTTPS.
2. **Use `DaemonControl` / Pyro** when code runs on the Mycodo host and needs
   daemon operations with Python return values, especially Output, Input, PID,
   Function Action, Widget, and daemon control calls.
3. **Use `mycodo-client`** when operating locally from shell scripts, service
   hooks, or manual maintenance and the installed command is available.
4. **Use multi-channel REST** when a client needs the latest values for several
   sensor channels in one InfluxDB-backed request.
5. **Do not automate hardware-changing operations** until the user confirms the
   target Output/Input/PID/controller ID, channel, duration/duty cycle/volume,
   and the physical safety consequence.

## Bundled Files

Read or run these files instead of looking up upstream material:

- [references/rest-api.md](references/rest-api.md) — read when building REST
  calls, selecting endpoint families, formatting `Accept`/auth headers, or
  interpreting status codes.
- [references/daemon-client.md](references/daemon-client.md) — read when using
  local Python `DaemonControl`, Pyro URI/timeout options, or `mycodo-client`
  command-line flags.
- [references/multi-channel-api.md](references/multi-channel-api.md) — read
  when batching measurement reads across multiple channels, sensors, or
  dashboard/mobile clients.
- [references/troubleshooting.md](references/troubleshooting.md) — read when a
  request returns 401/403/404/406/422/460/5xx, TLS errors, empty InfluxDB data,
  Pyro timeouts, or CLI/daemon failures.
- [scripts/mycodo_api_request.py](scripts/mycodo_api_request.py) — run for a
  reusable safe REST request helper that requires `--host`, `--endpoint`,
  `--method`, and an API key from `--api-key` or `MYCODO_API_KEY`. It defaults
  to `Accept: application/vnd.mycodo.v1+json`, prints status plus a small header
  subset, and pretty-prints JSON or text bodies.

## REST API Quick Contract

- Base URL: `https://<mycodo-host>/api/...`.
- Endpoint documentation for the installed instance is served at
  `https://<mycodo-host>/api`.
- All authenticated API calls are intended for HTTPS. Self-signed certificates
  are common on local Mycodo installs; use `curl -k`, `requests verify=False`,
  or the bundled helper's `--insecure` only for hosts the user trusts.
- Send `Accept: application/vnd.mycodo.v1+json` for API v1.
- Prefer `X-API-KEY: <base64-api-key-shown-in-user-settings>` for automation.
  The request loader also accepts `Authorization: Basic <same-base64-api-key>`
  and a query-string `api_key=<same-base64-api-key>`, but query strings are more
  likely to leak through logs.
- Treat examples that use `Authorization: Bearer <key>` as deployment-specific
  unless the live instance proves Bearer support; the inspected request loader
  authenticates API-key query, Basic, and `X-API-KEY` forms.

## Safe REST Workflow

1. Obtain the API key from web UI user settings; never embed real keys in skill
   files, logs, git commits, prompts, or examples.
2. Confirm endpoint documentation at `/api` on the target host and record the
   method, path, required permission, request body, and response shape.
3. Prefer read-only `GET` endpoints first: `/api/daemon/`, `/api/settings/...`,
   `/api/inputs/`, `/api/outputs/`, `/api/measurements/...`, and `/api/choices/...`.
4. For mutating `POST` endpoints, require explicit user confirmation of target
   IDs and physical effect: Output state/duty/volume, Input force measurement,
   controller activation, measurement creation, note creation, or daemon
   termination.
5. Check status codes before assuming success. `2xx` means success; `4xx` means
   request/auth/permission/payload problems; `5xx` means server-side failure.
   Mycodo can return `460` when a daemon operation reports failure.

## Local Daemon Workflow

Use local daemon access only on a trusted Mycodo host where the Mycodo package,
configuration, database, and Pyro daemon are available. The default Pyro URI is
`PYRO:mycodo.pyro_server@127.0.0.1:9080`; it is not an HTTPS remote API. The
public installed layout commonly uses `/opt/Mycodo` and an environment under
`/opt/Mycodo/env`, but always follow the user's installed layout.

Typical decision points:

- Need daemon health, RAM use, or virtualenv status: REST `/api/daemon/`,
  `DaemonControl().check_daemon()`, or `mycodo-client --checkdaemon`.
- Need Output state/change with Python return values: use `DaemonControl` or
  REST `/api/outputs/<output_id>`; include `output_channel`/`channel`.
- Need a shell-friendly one-shot: use `mycodo-client`, but avoid irreversible
  flags such as daemon termination unless explicitly approved.

## Automation Safety Checklist

Before sending any request or local daemon command that can mutate state:

- Confirm the target Mycodo host is the intended system, not a production system
  confused with a test system.
- Confirm the controller type and exact unique ID: Input, Output, Function,
  Action, Widget, Dashboard, PID, Conditional, or Trigger.
- Confirm channel numbers are zero-based where relevant.
- Confirm units, measurement names, and InfluxDB time windows for measurement
  reads.
- Confirm the API key belongs to a user role with only the necessary permission.
- Confirm TLS behavior: use certificate verification when possible; use
  `--insecure`/`-k` only for trusted local/self-signed hosts.
- Stop before changing system services, nginx, InfluxDB, Docker, GPIO/I2C/UART,
  1-Wire, Bluetooth, camera, backup/restore, or installer state without
  explicit user authorization.

## Verification Limits

This skill was produced from CPU/source inspection of the repository and bundled
runtime evidence. Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera behavior,
systemd/nginx/InfluxDB services, Docker deployment, backup/restore operations,
and full installer execution were not exercised. Treat those as operational
surfaces that require live-system confirmation before mutation.

## Minimal Examples

Read-only request with the bundled helper:

```bash
MYCODO_API_KEY="<base64-key-from-user-settings>" \
python scripts/mycodo_api_request.py \
  --host https://mycodo.local \
  --endpoint /api/daemon/ \
  --method GET \
  --insecure
```

Read-only `curl` pattern:

```bash
curl -k -sS "https://mycodo.local/api/settings/inputs" \
  -H "Accept: application/vnd.mycodo.v1+json" \
  -H "X-API-KEY: <base64-key-from-user-settings>"
```

Local Python daemon probe:

```python
from mycodo.mycodo_client import DaemonControl
control = DaemonControl(pyro_timeout=10)
print(control.check_daemon())
```

If any example fails, use [references/troubleshooting.md](references/troubleshooting.md)
before retrying with broader permissions or mutating commands.
