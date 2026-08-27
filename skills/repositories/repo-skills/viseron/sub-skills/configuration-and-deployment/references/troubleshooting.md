# Troubleshooting Configuration and Deployment

## Purpose

Use this when deployment, YAML parsing, secrets, webserver/authentication, reverse proxy, logging, reload, safe mode, live-view access, or public image URL behavior fails. The steps below avoid starting Viseron unless explicitly noted.

## Quick triage order

1. Run the bundled YAML/secrets preflight:
   ```bash
   # From this sub-skill directory, or by resolving the bundled script path from the loaded skill.
   python scripts/validate_config_yaml.py /path/to/config.yaml
   ```
2. Confirm `config.yaml` and `secrets.yaml` are in the same mounted config directory.
3. Replace top-level null entries with explicit `{}` while debugging.
4. Check container logs and the `viseron.log` file in the config directory.
5. If Viseron is running, check whether the WebSocket/system information or logs report `safe_mode`.
6. Only then reload or restart the container.

## YAML and secrets failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `!secret found in config.yaml, but no secrets.yaml exists` | `config.yaml` references secrets but no adjacent `secrets.yaml` is mounted. | Create `secrets.yaml` next to `config.yaml`; rerun the bundled validator; restart/reload after validation passes. |
| `secret <name> does not exist in secrets.yaml` | Key typo, indentation error, or wrong secrets file. | Add the missing key exactly, keep values as scalars unless a component expects structured data, and rerun the validator. |
| YAML parser error | Indentation, tabs, invalid inline mapping/list, or unquoted colon in a scalar. | Validate the smallest changed section first. Use the UI editor for syntax highlighting if Viseron is reachable. |
| Top-level component is `null` | YAML key written as `webserver:` or `nvr:` with no value. | Viseron normalizes this to `{}`, but use `webserver: {}`/`nvr: {}` for clarity. |
| Empty or default walkthrough config starts with only Web UI/default services | No real component config was provided yet. | This is expected. Add cameras/NVR/detectors in their owning sub-skills only when ready. |

### Difficult case: missing secret plus reverse-proxy subpath

If a user reports both an unreachable `/viseron/` proxy and a config load failure:

1. Validate secrets first. A missing secret can prevent Viseron from loading far enough for webserver/proxy symptoms to be meaningful.
2. Use a minimal config containing only:
   ```yaml
   webserver:
     subpath: /viseron
     auth: {}
   logger:
     default_level: info
   ```
3. Validate again. If it passes, test the proxy path and WebSocket upgrade. Then reintroduce cameras/detectors one section at a time.

## Safe mode and critical startup failures

Viseron enters safe mode when config loading fails or a critical component fails to load. In safe mode it attempts to load the last known good critical-component config; if none exists, it uses default critical services. Symptoms include logs mentioning safe mode, a WebSocket `system_information.safe_mode` value of `true`, and missing camera/detector/integration functionality.

Recovery:

1. Do not immediately delete config or auth state.
2. Validate YAML and secrets with the bundled script.
3. Temporarily reduce to a camera-less debug config:
   ```yaml
   webserver: {}
   logger:
     default_level: debug
     logs:
       viseron.components: debug
   ```
4. Restart or reload and confirm the Web UI/default services work.
5. Reintroduce non-critical workflows section by section. Route camera/NVR issues to `camera-recording-pipeline`, detector issues to `detection-and-ai-components`, and integrations to `automation-and-integrations`.

## Webserver and reverse proxy failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| UI works at direct host port but static assets/API fail under `/viseron/` | Proxy path and `webserver.subpath` mismatch, or proxy does not strip the subpath. | Set `webserver.subpath: /viseron`; configure the proxy location for `/viseron/`; forward upstream to the service root with a trailing slash. |
| Web UI loads but live updates/API subscriptions fail | Missing WebSocket upgrade headers through proxy. | Add HTTP/1.1 upgrade headers and confirm the proxy supports WebSocket pass-through. |
| Generated recording/snapshot links miss the subpath | Ingress/proxy headers or configured subpath are missing. | Prefer the proxy's ingress header when available; otherwise set `webserver.subpath` exactly. |
| Host port is occupied | Docker host port collision or direct Python development port collision. | Change the host-side Docker/Compose port mapping. Treat `webserver.port` as deprecated, not the primary fix. |
| Public image URL cannot be opened externally | `public_base_url` missing or not externally reachable; proxy blocks `/files` URLs; auth/proxy policy blocks public image endpoint. | Set `public_base_url` to the external base, verify URL expiry/download limits, and test through the same proxy path users will receive. |

## Authentication and authorization failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| First login redirects to onboarding | Auth was just enabled and no admin user exists. | Complete onboarding in the Web UI. |
| Admin password lost | Only admin credentials are unavailable. | Back up config state, then delete the auth/onboarding state files in the mounted config state and restart. This deletes all users. |
| API returns unauthorized | Auth enabled but no valid personal access token or browser session. | Generate a PAT from the Profile page and use it in the Authorization header. |
| WebSocket returns auth-required/auth-failed | Client did not send a valid token in the handshake. | Send the expected auth message with a current access token before commands/subscriptions. |
| HTTP 429 on login/token/onboarding | Rate limit exceeded, often due to repeated bad credentials or many clients behind one IP. | Wait for the configured window or tune `auth.rate_limits` only after confirming legitimate traffic. |
| Last admin cannot be removed or demoted | Safety rule prevents losing all admin access. | Create another admin first, then modify the original account. |

## Logging failures and noisy diagnostics

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Too much log noise after setting `default_level: debug` | Global debug applies broadly. | Use `logger.logs.<namespace>` or `logger.cameras.<camera_identifier>` instead. |
| Camera-specific debug did not apply | Camera identifier spelling does not match the configured camera slug, or logger was not reloaded. | Use the exact lowercase/underscore camera identifier and reload config. |
| Rotation env var ignored | Invalid size suffix or non-numeric value. | Use values like `100mb` and integer backup counts. Check logs for parse fallback. |
| Secrets appear in logs | Sensitive-information filtering should redact common secrets, but avoid pasting real credentials into config examples or support output. | Use `!secret` and redact logs before sharing. |

## Live view and snapshot access failures owned here

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Live page falls back to MJPEG or has higher latency | `go2rtc` is not configured. | For WebRTC/MSE, route stream setup to `camera-recording-pipeline`. |
| MJPEG stream unavailable for a camera | The camera is configured with `record_only: true` or frames are not being decoded. | Use Events/Timeline HLS for recordings or change camera pipeline settings in `camera-recording-pipeline`. |
| Snapshot downloads/public links fail through proxy | Subpath/public base URL/proxy files route mismatch. | Fix `webserver.subpath`, `public_base_url`, and proxy routing before investigating detector snapshot generation. |

## Template and system-event confusion

- The System Events viewer is the safest way to inspect event payload fields before writing templates.
- Templates can use `states` and, for event-triggered components, `event`.
- Conditions are true for boolean true, non-zero numbers, and strings such as `true`, `yes`, `on`, or `enable` case-insensitively.
- If template rendering fails during admin WebSocket rendering or an automation action, route the action-specific payload/condition design to `automation-and-integrations` after confirming webserver/auth access here.
