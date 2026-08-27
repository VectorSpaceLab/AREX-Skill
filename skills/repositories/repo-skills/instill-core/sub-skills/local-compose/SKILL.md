---
name: local-compose
description: "Guides Instill Core local Docker Compose startup, service
  lifecycle, ports, logs, and overlay debugging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Local Compose

Use this route when the user wants the local platform stack started, stopped, inspected, or debugged with Docker Compose.

## Use this when the request mentions

- `make run`, `make compose-run`, or `make compose-dev`.
- `make down`, `make start`, `make stop`, `make ps`, `make logs`, `make pull`, `make images`, or `make top`.
- Docker Compose files such as `docker-compose.yml`, `docker-compose-dev.yml`, `docker-compose-nvidia.yml`, or `docker-compose-observe.yml`.
- Service port, health, or container-name questions for the local stack.
- GPU-vs-CPU compose selection or observability overlays.

## What belongs here

- Starting and stopping the stack.
- Inspecting service status, logs, and ports.
- Understanding the dev overlay, GPU overlay, and observability overlay.
- Checking the main health endpoints and service dependencies.

## What does not belong here

- Helm or Kubernetes deployment; use [helm-deployment](../helm-deployment/SKILL.md).
- Dummy model build/push or model initialization; use [integration-tests](../integration-tests/SKILL.md).
- Version bump or release automation; use [release-maintenance](../release-maintenance/SKILL.md).
- Backend source code edits in sibling service repositories.

## Core workflow

1. Run `../../scripts/check-toolchain.sh --mode compose --repo-root <checkout>`.
2. Confirm the intended edition and overlay set in `../../references/configuration.md`.
3. Use `make run` for the default local stack or `make compose-dev` for the dev overlay.
4. Use `make ps`, `make logs`, `make stop`, `make start`, `make pull`, `make images`, and `make top` to inspect or manage the stack.
5. Use `make down` before retrying a failed run so stale containers and volumes do not interfere.

## Quick decision cues

- Choose `make run` for the default local stack.
- Choose `make compose-dev` when you want the debug overlay and the published backend ports.
- Choose `OBSERVE_ENABLED=true make run` when you need Grafana, Prometheus, Tempo, Loki, and the collector overlay.
- On GPU-capable hosts, remember that the Makefile auto-selects the NVIDIA compose path and therefore expects `yq`.
- If the same stack was interrupted earlier, clear it with `make down` before trying again.

## Common mistakes

- Assuming the backend service source code lives in this repository.
- Forgetting to inspect the active `.env` file and secrets files before the first boot.
- Forgetting that the GPU overlay is selected automatically when `nvidia-smi` is present.
- Skipping `make down` after a half-failed run and then reading stale logs from the wrong containers.

## If the request is mixed or unclear

- Choose this route if the user wants the container stack up or down, even if they also mention ports or logs.
- If the user is talking about chart rendering or Kubernetes, send them to the Helm route instead.
- If the user is talking about dummy models or registry population, send them to the integration-tests route instead.
- When the user only needs the command surface, the Makefile targets in this route are usually enough.

## Read these references

- [workflows](references/workflows.md) for the command map and local-stack startup sequence.
- [troubleshooting](references/troubleshooting.md) for Docker, port, GPU, and env-file failures.
- [configuration](../../references/configuration.md) for ports, health probes, and overlays.
- [check-toolchain.sh](../../scripts/check-toolchain.sh) before the first retry.

## Useful commands

- `make run` launches the stack with the default edition.
- `make compose-run EDITION=docker-ce:test` matches the Compose integration-test edition.
- `make compose-dev` adds the development overlay.
- `OBSERVE_ENABLED=true make run` adds the observability overlay.

## Exit criteria

A future agent should be able to start the stack, confirm the main ports and health probes, and cleanly stop the stack without reopening the original repository docs.
