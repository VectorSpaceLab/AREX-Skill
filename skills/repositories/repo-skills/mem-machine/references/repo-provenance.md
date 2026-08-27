# Repo Provenance

Schema: `disco.repo-provenance.v1`

This generated operating skill was distilled from the public MemMachine
repository. It is self-contained runtime guidance; the original checkout is not
required to use the skill.

## Source Snapshot

- Repository: MemMachine / MemMachine
- Public remote: `https://github.com/MemMachine/MemMachine.git`
- Commit: `2d28c1c1e57d1026335c4a829b1a9b0a918c114f`
- Branch: `main`
- Exact tag: none detected at the source snapshot
- Package version baseline: `0.1.dev1+g2d28c1c1e`
- Working tree at evidence capture: clean source tree; generated `skills/`
  outputs were added after evidence capture and are not upstream source input.

## Evidence Paths

The skill distilled evidence from these relative source paths:

- `README.md`, `USAGE.md`, `DOCKER_COMPOSE_README.md`, `STYLE_GUIDE.md`,
  `AGENTS.md`
- `pyproject.toml`, `uv.lock`, and package `pyproject.toml` files under
  `packages/`
- `packages/common/src/memmachine_common/`
- `packages/client/src/memmachine_client/`
- `packages/client/client_tests/`
- `packages/server/src/memmachine_server/`
- `packages/server/server_tests/`
- `packages/meta/`
- `packages/ts-client/src/`, `packages/ts-client/tests/`, and
  `packages/ts-client/package.json`
- `docs/api_reference/`, `docs/getting_started/`, `docs/install_guide/`,
  `docs/open_source/`, `docs/examples/`, `docs/platform/`, `docs/tools/`,
  `docs/openapi.json`, and `docs/platform.openapi.json`
- `sample_configs/`, `docker-compose.yml`, `memmachine-compose.sh`,
  `build-docker.sh`, and `deployments/helm/`
- `examples/`, `integrations/`, and `tools/chatgpt2memmachine/`
- Existing repo-local guidance under `packages/skills/memmachine-memory/`

## Refresh Triggers

Refresh this skill when any of these change materially:

- Python SDK signatures or CLI commands in `memmachine_client`
- REST endpoint paths, common API models, or filter syntax in
  `memmachine_common` / server routers
- Server configuration schema, resource providers, optional extras, or MCP
  entry points
- TypeScript client constructor defaults, method names, option names, or Node
  engine requirements
- Framework integration APIs or migration-tool input formats
- Package version, public installation instructions, or required service
  topology
