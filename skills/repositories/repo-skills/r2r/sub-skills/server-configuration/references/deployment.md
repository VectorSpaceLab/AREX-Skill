# Deployment Reference

## Python server

- Prefer a safe import probe first: `python scripts/check_r2r_environment.py`
- Run the server only after config and database settings are in place.
- Use `python -m r2r.serve` or the `r2r-serve` console script for the actual server launch.

## Docker light mode

```bash
docker compose -f docker/compose.yaml --profile postgres up
```

## Docker full mode

```bash
docker compose -f docker/compose.full.yaml --profile postgres up
```

## Service stack hints

- R2R API
- Postgres
- MinIO or other object storage used by the stack
- Hatchet / orchestration services in full mode
- unstructured / clustering services when enabled
- dashboard or user-facing UI when included by the compose profile

## Operational checks

- confirm `/v3/health` after startup
- confirm the database and object-storage services are reachable before starting orchestration-heavy flows
- mount user config or tool directories only when the deployment asks for them
