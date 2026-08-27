# Gateway Lifecycle

## Core commands

- `opensquilla gateway run` — foreground gateway; stop it with `Ctrl+C`.
- `opensquilla gateway start --json` — managed background gateway with readiness wait.
- `opensquilla gateway status` — inspect the managed gateway.
- `opensquilla gateway stop` — stop the recorded gateway gracefully.
- `opensquilla gateway restart` — restart the recorded gateway gracefully.
- `opensquilla gateway reload` — re-read the on-disk config into a running gateway.

## What each command is for

Use `run` for a single terminal session and `start --json` when the gateway should keep running after the shell returns.
Use `status` to confirm the current bind, port, and process state.
Use `stop` and `restart` when you need the gateway to drain in-flight turns and background work before it exits.
Use `reload` only when you edited the config on disk and want to hot-apply the parts the gateway can reload live.

`reload` is not a full replacement for restart: channel changes, memory-embedding changes, and sandbox-posture changes still require `opensquilla gateway restart`.

## Bind and port

Default gateway address:

```text
http://127.0.0.1:18791/control/
```

Default bind behavior is loopback-only for safety.

- `--port` changes the port.
- `--listen` changes the bind host and wins over `--bind`.
- `OPENSQUILLA_LISTEN` wins over `OPENSQUILLA_GATEWAY_HOST` when no explicit flag is supplied.
- The config file host is the last fallback before the default loopback bind.

If the port is busy, try another one:

```sh
opensquilla gateway run --port 18792
```

For remote inspection, point `status` at an explicit gateway URL:

```sh
opensquilla gateway status --gateway ws://localhost:18791/ws
```

## Safe exposure

Binding to a wildcard address is opt-in:

```sh
opensquilla gateway run --listen 0.0.0.0 --port 18791
```

Only do this behind token auth and a network boundary you trust.
When a wildcard-bound gateway is reached through a custom DNS name or reverse proxy, list the exact browser origin in `cors.allowed_origins`.

Do not treat `auth.mode=none` plus a wildcard bind as safe public exposure — that makes the gateway LAN-open.

## Restart after these changes

Restart the gateway after changing:

- provider or router configuration
- channel configuration
- durable agent entries
- sandbox posture
- search or image-generation setup
- environment variables used by configured providers

```sh
opensquilla gateway restart
```
