# Deployment and Operations

## Deployment Shapes

| Shape | Use when | Notes |
|---|---|---|
| `uvx langbot` | Quick package evaluation | Creates `data/` in the current directory. |
| Source checkout | Development/customization | Run backend with `uv`, frontend separately with `pnpm`. |
| Docker Compose basic | Self-hosted deployment without Box | Starts main LangBot service. |
| Docker Compose `all` / Box profile | Full agent tools, Box, stdio MCP hosting, skill add/edit | Adds Plugin Runtime and Box Runtime services. |
| Kubernetes | Production/container orchestration | Mirror Compose topology and secrets. |

## Runtime Services

- Main LangBot service: HTTP API, MCP, and web UI on `api.port` (default 5300).
- Plugin Runtime: control endpoint commonly on port 5400 and debug endpoint on
  5401 when standalone/containerized.
- Box Runtime: endpoint commonly on port 5410 when standalone/containerized.

Containerized deployments should align host/container Box workspace paths and
control tokens. Box failures often come from Docker socket permission or
mismatched `BOX__LOCAL__HOST_ROOT`, not from Python code.

## Operational Health

`/healthz` exposes aggregate counters such as task manager state, query pool,
runtimes, database pool, blocking executor, event-loop metrics, and service
cardinality. Use this before deep debugging.

Resource probe scripts in the source repository are intentionally heavy:

- `runtime_resource_probe.py`: registry plateau under churn.
- `workspace_runtime_capacity_probe.py`: populated Workspace replacement cost.
- `cloud_runtime_soak.py`: production-candidate Core/Plugin/Box/cgroup soak.

Treat these as reference-only unless the task is explicitly about production
resource retention. Prefer their quick scale before audit/24h gates.

## Environment Variables

LangBot config supports environment override patterns such as `BOX__ENABLED`,
`BOX__BACKEND`, and similar nested config overrides. Prefer deployment-specific
env vars over editing committed templates for secrets or machine-local paths.

Never commit API keys, control tokens, provider keys, OAuth credentials, or
machine-local Box roots. Generated skills should describe the key names and
risk, not store values.

## Deployment Validation Checklist

1. `langbot --help` works in the runtime image/environment.
2. `data/config.yaml` or env overrides include expected `api`, `database`,
   `plugin`, and `box` settings.
3. `/healthz` responds.
4. Web UI loads or frontend assets are present.
5. Plugin Runtime and Box Runtime statuses match the configured standalone/local
   mode.
6. API/MCP auth is configured with a user token/API key/global key appropriate
   for the deployment.
7. If Box is enabled, Docker/nsjail/E2B prerequisites and shared workspace paths
   are valid.
