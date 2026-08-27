# Airweave provenance

This file records the source snapshot used to build the Airweave repo skill tree.

## Source snapshot

- Repository: Airweave
- Commit: `1ebe1af2dbfb90f3334410721e69997e4f02b320`
- Branch: `main`
- Exact tag: `v0.9.73`

## Construction scope

The generated skill tree was based on the repository surfaces inspected during distillation:
- backend service, schemas, and e2e smoke tests
- frontend dashboard source
- Connect widget source and tests
- MCP server source and tests
- Monke runner, bongos, configs, and generation code
- README, CLAUDE guidance, docker/vespa helpers, examples, and the top-level startup script

## Exclusions

The runtime skill tree intentionally excludes:
- `.git/`, caches, `node_modules`, and other generated artifacts
- credentialed or destructive maintenance scripts that are not safe as bundled defaults
- backend Alembic migration history as a runtime dependency
- private checkout paths and private environment paths

## Notes

This provenance file documents the source snapshot only. It is not a full build manifest and it is not intended to reproduce local environment state.
