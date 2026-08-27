# Repo Provenance

schema: `disco.repo-provenance.v1`

This generated operating skill was distilled from a RocketRide Server checkout.

## Source snapshot

- Repository: `rocketride-org/rocketride-server` (public URL from package metadata: `https://github.com/rocketride-org/rocketride-server.git`)
- Commit: `4a72f8d142d949010a25e34f42eb5f7802f040ea`
- Branch: `develop`
- Exact tag at HEAD: `client-mcp-v1.2.0-prerelease`
- Root package: `rocketride-server` version `3.3.0`
- Python SDK distribution: `rocketride` version `1.3.0`
- TypeScript SDK package: `rocketride` version `1.3.0`
- MCP distribution: `rocketride-mcp` version `1.2.0`
- VS Code extension version: `1.2.0`
- n8n nodes package version: `0.1.0`

## Dirty state

The working tree was dirty at skill completion because this construction run created generated files under `skills/`. No source-code changes outside `skills/` were part of the construction baseline.

## Evidence paths

The following repo-relative sources informed the generated skill:

- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `package.json`, `pnpm-workspace.yaml`, `pyproject.toml`
- `packages/docs/content-static/quickstart.mdx`, `concepts/pipelines.md`, `concepts/nodes.md`, `self-hosting.md`, `cli.mdx`, `troubleshooting.md`
- `packages/client-python/docs/`, `packages/client-python/src/rocketride/`, `packages/client-python/tests/`
- `packages/client-typescript/docs/`, `packages/client-typescript/src/client/`, `packages/client-typescript/contract/`, `packages/client-typescript/tests/`
- `packages/client-mcp/docs/`, `packages/client-mcp/src/rocketride_mcp/`, `packages/client-mcp/tests/`
- `packages/server/docs/`, `packages/server/CMakeLists.txt`, `packages/server/scripts/tasks.js`
- `nodes/src/nodes/`, `nodes/scripts/tasks.js`, `nodes/test/`
- `examples/`, `pipelines/`
- `apps/vscode/`, `apps/*-ui/`, `packages/shell/`
- `packages/n8n-nodes/`, `examples/n8n/`
- `docker/`, `deploy/helm/rocketride/`, `deploy/helm/examples/`
- `scripts/`, `tools/contract_checks/`, `tools/sync_models/`

## Verification baseline

The verified construction scope covers CPU/static package inspection and skill usability checks. Optional external services, Cloud accounts, model-provider keys, vector databases, Docker/Kubernetes clusters, VS Code runtime behavior, n8n runtime behavior, and GPU execution were documented but not claimed as verified.
