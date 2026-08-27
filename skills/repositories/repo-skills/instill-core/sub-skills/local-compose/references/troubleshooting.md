# Local Compose Troubleshooting

## Missing Docker or Compose

**Symptoms**: `docker: command not found`, `docker compose` fails, or the stack never starts.

**Likely cause**: Docker Engine or the Compose v2 plugin is not installed or not running.

**Recovery**: Install or start Docker, then rerun `scripts/check-toolchain.sh --mode compose --repo-root <checkout>` and retry the chosen `make` target.

## GPU host selected the NVIDIA compose path but `yq` is missing

**Symptoms**: The stack fails only on a GPU-capable host, often while the Makefile is preparing `docker-compose-nvidia.yml`.

**Likely cause**: The Makefile detected `nvidia-smi` and expected `yq` to patch the NVIDIA overlay.

**Recovery**: Install `yq` or move to a CPU-only environment where the GPU probe is absent. Then retry `make run` or `make compose-dev`.

## Stale containers or ports are already in use

**Symptoms**: Port-binding errors on 8080, 3000, 8081-8084, 5432, 6379, or other compose ports; health checks time out immediately; a rerun refuses to start.

**Likely cause**: A previous compose session is still running, or its ports were not released.

**Recovery**: Run `make down`, then retry. If the failure happened after an interrupted run, also inspect any leftover container names in `make ps` or `docker ps -a`.

## Health checks do not become ready

**Symptoms**: API gateway, pipeline, model, artifact, or mgmt health probes never return healthy.

**Likely cause**: One dependency in the compose graph is not ready, or a secret/config value in `.env` is inconsistent with the stack.

**Recovery**: Use `make logs` and inspect the relevant container health endpoint from `references/configuration.md`. If the stack is dirty, run `make down` and retry from a clean state.

## Console or backend configuration looks wrong

**Symptoms**: A service starts with the wrong edition, missing URLs, or no component secrets.

**Likely cause**: The active `.env` file or secrets file does not match the intended Compose profile.

**Recovery**: Verify the edition and secrets files in the target checkout, then rerun the chosen compose command.
