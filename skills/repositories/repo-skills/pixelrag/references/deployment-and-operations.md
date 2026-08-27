# Deployment and Operations

PixelRAG's public repo documents production topology but intentionally excludes host-specific secrets, hostnames, and live state.

## Topology

- Frontend: `web/`, deployed separately.
- Search API: `pixelrag serve` behind nginx, using blue-green slots.
- Chat agent: Node service that calls the search API.

## Blue-green search API concept

Two API slots run on different ports. To roll out a new index/model safely:

1. Bring up the idle slot with the new config.
2. Health-check and smoke-test the target.
3. Switch nginx upstream with a graceful reload.
4. Restart/repoint the chat agent.
5. Roll back by switching to the previous port.

Do not restart a loaded slot in place when index reload time would cause downtime.

## Safety boundaries

The repo's deploy scripts can:

- Fast-forward a checkout.
- Run dependency sync.
- Restart services.
- Rewrite nginx upstream configuration.
- Switch systemd blue/green slots.

Only run them when the user confirms this is the deploy host and asks for operational changes. Otherwise treat deployment files as reference material for understanding production architecture.

## Operational checks before service changes

- Confirm clean `main` checkout if following the documented deploy workflow.
- Confirm which slot is active and which is idle.
- Check `/health` and `/status` on the candidate API.
- Run a small `/search` smoke against the candidate.
- Keep rollback port and previous config available.

## Relation to this repo skill

For normal Researcher package tasks, prefer:

- `sub-skills/index-build/` to create or inspect indexes.
- `sub-skills/serve-search/` to start/query a development API.
- This reference only when the user asks about production deployment, blue-green cutover, or chat-agent topology.
