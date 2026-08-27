# Repo Provenance

- Schema: `disco.repo-provenance.v1`
- Repository: Bindu
- Public remote: `https://github.com/GetBindu/Bindu.git`
- Source commit: `7b1ff75ac93f3b3eb94b975f727bdee9436cc7ce`
- Branch: `main`
- Exact tag: none recorded at skill creation time
- Working tree state at analysis: clean
- Distribution name: `bindu`
- Import root: `bindu`
- Package version observed from editable install metadata: `0.3.15.dev1+g7b1ff75ac`
- Python requirement: `>=3.12`
- Console script: `bindu = bindu.cli:main`

## Evidence paths

The skill was distilled from these relative repository paths:

- `README.md`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, `pytest.ini`, `.pre-commit-config.yaml`
- `bindu/` package source, excluding generated stubs as primary source
- `proto/agent_handler.proto`
- `docs/`, especially auth, DID, security, payment, skills, negotiation, gRPC, runtime, storage, scheduler, observability, tunneling, and gateway documentation
- `examples/` for user-facing agent patterns; credentialed examples were not executed
- `sdks/typescript/` for TypeScript SDK API and gRPC callback flow
- `gateway/` and `inbox/` for orchestration and operator UI workflows
- `scripts/`, `gateway/scripts/`, `inbox/scripts/` for source-script inventory and reference-only workflows
- `.agents/skills/` for repository-maintenance playbook conventions
- `tests/unit/` and selected `tests/integration/`/`tests/e2e/` files for behavior evidence and native verification candidates

## Refresh signals

Refresh this repo skill when any of these change materially:

- `pyproject.toml` dependencies, package name, console script, or Python requirement
- `bindu.penguin.bindufy`, manifest creation, task manager/worker, storage/scheduler, auth, payment, mTLS, runtime, or gRPC modules
- `proto/agent_handler.proto` or generated-stub policy
- TypeScript SDK config/handler types or registration lifecycle
- Gateway `/plan` schema, recipe loader, peer-auth config, or Inbox process/port model
- Public docs for auth, DID, x402, private skills, runtime-boxd, Gateway, Inbox, or repository contribution policy
