# Webserver, Logging, and Authentication

## Purpose

Use this reference when the user's task mentions the Web UI, reverse proxy, API tokens, authentication, auth rate limits, public image URLs, or Viseron logging. Keep camera streams, recording tiers, detectors, and notification actions in their owning sub-skills.

## Webserver configuration

The `webserver` component is a default component and serves the frontend, REST API, WebSocket API, MJPEG stream endpoints, static/public files, and admin commands such as config save/reload. It is enabled even when not present in `config.yaml`; add the key only when changing defaults:

```yaml
webserver: {}
```

Important options:

| Option | Meaning | Notes |
| --- | --- | --- |
| `debug` | Enables Tornado/webserver debug behavior | Do not use in production; it weakens security. |
| `subpath` | URL prefix when served behind a reverse proxy | Normalized to start with `/`, strip trailing `/`, and collapse repeated leading slashes. Use `/viseron`, not `/viseron/`. |
| `public_base_url` | Base URL used to generate externally reachable public image links | Must match the externally reachable HTTPS URL when notifications need public images. |
| `public_url_expiry_hours` | Expiration for generated public image URLs | Default 24; maximum 744 hours. |
| `public_url_max_downloads` | Download limit for public image URLs | `0` means unlimited downloads until time expiry; `1` makes a single-use URL. |
| `auth` | Enables built-in user authentication | Empty `{}` is enough to enable onboarding. |
| `port` | Deprecated schema option | Prefer Docker/Compose host port mapping or reverse proxy configuration. |

### Reverse proxy subpath checklist

For a service exposed as `https://example.invalid/viseron/`:

```yaml
webserver:
  subpath: /viseron
```

Proxy requirements:

- Match the external path and configured `subpath` exactly.
- Strip the subpath before forwarding to Viseron; Nginx-style `proxy_pass` should end with `/`.
- Preserve `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto` if the proxy supports them.
- Enable WebSocket upgrade headers; otherwise live updates and WebSocket API behavior can fail.
- Home Assistant ingress can provide an `X-Ingress-Path` header; Viseron uses that header before the configured subpath for generated URLs.

## Authentication

Authentication is disabled by default. Enable it with:

```yaml
webserver:
  auth: {}
```

On first access after enabling auth, the frontend prompts onboarding to create the first admin user. Roles are:

- `admin`: full settings/config/user access.
- `write`: can perform delete/write operations but cannot change settings.
- `read`: view-only access.

Users can be assigned to specific cameras from the user-management UI. Personal access tokens for REST/API clients are created from the Profile page; when auth is enabled, REST calls use an `Authorization` header with that token. WebSocket clients receive an auth-required message and must respond with an access token before subscribing or issuing commands.

### Session expiry and rate limits

Use `session_expiry` to force browser sessions to expire after a fixed absolute lifetime:

```yaml
webserver:
  auth:
    session_expiry:
      days: 30
```

Auth-sensitive endpoints have in-memory, per-IP sliding-window rate limits. Defaults are login `10/60s`, token refresh `30/60s`, and onboarding `5/60s`:

```yaml
webserver:
  auth:
    rate_limits:
      login:
        max_attempts: 10
        window_seconds: 60
      token:
        max_attempts: 30
        window_seconds: 60
      onboarding:
        max_attempts: 5
        window_seconds: 60
```

Tune these up only when many legitimate clients share one source IP; tune them down for a stricter public edge. Rate-limit state is in memory and resets on restart.

### Resetting the only admin account

If the only admin password is lost, the documented reset path is to delete the onboarding/auth state files inside the mounted configuration state and restart. This deletes all users and forces onboarding again. Treat this as destructive recovery; back up the config volume first and do not remove user/auth state casually.

## Logging

Viseron enables console logging and a rotating `viseron.log` file inside the config directory. The `logger` component controls runtime log levels:

```yaml
logger:
  default_level: info
  logs:
    viseron.components.ffmpeg: debug
  cameras:
    camera_one: debug
```

Available levels, from most to least severe: `critical`, `error`, `warning`, `info`, `debug`.

Precedence is:

1. `logger.cameras.<camera_identifier>` applies to loggers whose dot-separated logger name contains that camera identifier.
2. `logger.logs.<logger_name>` applies to a specific logger namespace.
3. `logger.default_level` applies globally.

Debugging tips:

- Avoid global `debug` unless collecting a short trace; it is noisy.
- Prefer camera-specific debug when one camera is failing.
- Prefer component namespace debug when a component family is failing, such as `viseron.components.webserver` or `viseron.components.storage`.
- The logger component applies reload deltas instead of resetting all loggers, so a config reload can be enough for many logging changes.

Log rotation can be controlled with container environment variables:

```yaml
services:
  viseron:
    environment:
      - VISERON_LOG_MAX_BYTES=100mb
      - VISERON_LOG_BACKUP_COUNT=5
```

`VISERON_LOG_MAX_BYTES` accepts suffixes such as `b`, `kb`, `mb`, `gb`, and `tb`. Invalid values fall back to defaults and emit an error.

## API and WebSocket basics

The Web UI communicates through REST and WebSocket APIs served by the webserver. The REST API is not a stable fully documented public contract, so prefer the Web UI for administrative operations unless the user specifically asks for API automation.

Auth behavior:

- With auth disabled, basic UI/API access does not require login.
- With auth enabled, REST calls require an access token and WebSocket clients must complete the token handshake.
- WebSocket `auth_ok` responses include system information such as version, git commit, and whether Viseron is in safe mode.
- Admin-only WebSocket commands include reading/saving config, reloading config, restarting Viseron, and rendering templates.

When a user asks for webhook payloads, notification templates, MQTT topics, or automation actions, route to `automation-and-integrations` after confirming the webserver/auth prerequisites here.
