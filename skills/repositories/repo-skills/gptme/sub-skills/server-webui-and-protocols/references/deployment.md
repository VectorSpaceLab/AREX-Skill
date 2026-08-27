# Deployment and sidecar

This reference covers the self-hosting shapes that show up most often in support: Docker Compose, reverse-proxy deployment, systemd service installs, and desktop sidecars.

## Docker Compose

The repo ships a Compose setup for the server and a separate computer-use environment. The important server-side patterns are:

- the server listens on the published `GPTME_SERVER_PORT` and always serves on its internal `5700` port
- at least one provider key must be present for useful conversations
- `GPTME_SERVER_TOKEN` should be stable for persistent deployments
- `CORS_ORIGIN` is only needed when the UI comes from a different origin
- the bundled UI is same-origin when the server and UI are served together

Operationally, the server container is the simplest path for a self-contained deployment. The computer-use container is separate and intentionally ephemeral.

## Reverse proxy deployment

For a public-facing deployment, keep the gptme server behind a TLS-terminating reverse proxy.

Rules of thumb:

- bind the server to loopback and let the proxy own the public socket
- keep bearer auth enabled
- forward the `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto` headers
- disable buffering for SSE responses
- use a long read timeout so streamed tokens reach the browser immediately

If proxy buffering stays on, chat appears to hang until the response finishes instead of streaming token by token.

## systemd service pattern

A persistent service install should use a dedicated service user, a stable token file, and a minimal writable surface.

Recommended pattern:

1. install the `gptme-server` entry point for the service user
2. pre-create the service user's config and data directories
3. store provider keys and `GPTME_SERVER_TOKEN` in a root-owned secret file with restricted permissions
4. run the server under systemd with hardening options enabled
5. allow writes only to the config, data, and state directories that the server actually needs

Keep the token stable. If the service generates a new token on every restart, client configs become stale immediately.

## Local-only access

If the server should only be reachable from the same machine or over a VPN/SSH tunnel, skip the public reverse proxy and keep the server on loopback. A plain SSH tunnel is often simpler than exposing the server publicly.

## Sidecar / parent-death behavior

Desktop integrations can launch `gptme-server` as a sidecar process. The server CLI includes:

- `--exit-on-parent-death`
- `--watch-pid <pid>`

Use these when a wrapper process can disappear without cleaning up children. This matters for Tauri and similar desktop shells, and it also matters when a bundled executable survives reparenting after the parent exits.

### Why this exists

If the parent vanishes but the server keeps running, the browser or desktop shell can leave behind an orphaned chat backend. The watcher forces a graceful shutdown path instead of letting the process linger.
