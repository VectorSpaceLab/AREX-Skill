# Server Troubleshooting

## Common issues

- **Missing Postgres env vars**: set the `R2R_POSTGRES_*` values before starting the server.
- **Provider key errors**: confirm the correct API key for the selected config.
- **Port conflicts**: check `R2R_PORT` and any Docker port mappings.
- **`r2r-serve` startup failure**: validate config and database settings before retrying.
- **Docker health failures**: verify the support services are up before treating the API as broken.
- **Full-mode orchestration delays**: some workflows are asynchronous and need time to settle.

## Recovery steps

1. Run `scripts/config_probe.py` on the config you intend to use.
2. Verify the database and provider settings.
3. If the issue is about client calls rather than server startup, route to the client sub-skills.
