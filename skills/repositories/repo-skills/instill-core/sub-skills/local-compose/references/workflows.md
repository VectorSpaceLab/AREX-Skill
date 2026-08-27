# Local Compose Workflows

## When to read

Read this when the user wants the stack running locally or needs to debug a Compose launch, port, or container issue.

## Start commands

| Command | What it does | Notes |
| --- | --- | --- |
| `make run` | Alias for `make compose-run` | Default entry point for local deployments. |
| `make compose-run` | Starts the full stack from `docker-compose.yml` | Uses the edition from `.env` unless overridden. |
| `make compose-dev` | Starts the stack with `docker-compose-dev.yml` | Enables debug ports and `CFG_SERVER_DEBUG=true`. |
| `OBSERVE_ENABLED=true make run` | Adds `docker-compose-observe.yml` | Starts Grafana, Prometheus, Tempo, Loki, and the collector stack. |

## Lifecycle commands

- `make ps` lists running containers.
- `make logs` tails the stack logs.
- `make stop` pauses running containers.
- `make start` resumes stopped containers.
- `make pull` refreshes the service images.
- `make images` lists the images in use.
- `make top` shows the running processes in each container.
- `make down` removes containers and volumes so the next run starts cleanly.

## Docker Compose overlays

- `docker-compose-dev.yml` publishes the private and public backend ports and enables debug mode.
- `docker-compose-nvidia.yml` is active only when the host exposes NVIDIA GPUs; the Makefile patches it with `yq` before `docker compose up`.
- `docker-compose-observe.yml` adds the observability services when `OBSERVE_ENABLED=true`.

## Local platform notes

- The Makefile auto-creates a `user_uid` file under `SYSTEM_CONFIG_PATH` when it is missing.
- The local stack expects the secrets files referenced by the Makefile and Compose manifests to exist before the first boot.
- The repository keeps the console, API gateway, backend services, database, cache, registry, and model runtime in one composed stack.
- If you need to change backend code, open the sibling service repository; this repo only orchestrates the containers.

## Validation checklist

- The main ports from `references/configuration.md` are reachable.
- `make ps` shows all expected containers healthy or starting.
- `make logs` shows the backend health checks reaching the ready state.
- `make down` clears the stack so a new run does not inherit stale containers or volumes.
