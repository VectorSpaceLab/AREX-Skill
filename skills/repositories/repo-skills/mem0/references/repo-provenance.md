# Repo Provenance

## Source Snapshot

- Repository: `mem0ai/mem0`
- Remote URL: `https://github.com/mem0ai/mem0`
- Commit: `4e448269bcf7136905b45c0ef5ac34c2254a1a3b`
- Branch: `main`
- Exact tag: none detected
- Dirty state before DisCo generation: clean for tracked files. Generated skill outputs are not part of the source baseline.

## Package Versions

| Package | Version | Runtime |
| --- | --- | --- |
| Python SDK distribution `mem0ai` | `2.0.7` | Python `>=3.10,<4.0` |
| TypeScript SDK package `mem0ai` | `3.0.9` | Node `>=18` |
| Python CLI `mem0-cli` | `0.2.8` | Python `>=3.10` |
| Node CLI `@mem0/cli` | `0.2.9` | Node `>=18` |
| Vercel AI provider `@mem0/vercel-ai-provider` | `3.0.0` | Node `>=18` |
| OpenClaw plugin `@mem0/openclaw-mem0` | `1.0.13` | Node package |
| Pi Agent plugin `@mem0/pi-agent-plugin` | `0.1.2` | Node package |

## Evidence Paths

- `pyproject.toml`
- `mem0/`
- `mem0-ts/package.json`
- `mem0-ts/src/`
- `cli/cli-spec.json`
- `cli/python/`
- `cli/node/`
- `server/`
- `openmemory/`
- `integrations/`
- `docs/`
- `examples/`
- `tests/`
- `skills/mem0/`
- `skills/mem0-cli/`
- `skills/mem0-vercel-ai-sdk/`
- `skills/mem0-integrate/`
- `skills/mem0-test-integration/`
- `skills/mem0-oss-to-platform/`

## Inspection Notes

A private Python inspection environment verified the local Python SDK package import, distribution metadata, and live signatures for `Memory`, `AsyncMemory`, `MemoryClient`, and `AsyncMemoryClient`. Private environment paths and local executable paths are intentionally omitted from this public provenance file.

## Refresh Signals

Refresh this skill if any of these change materially:

- Python SDK public signatures or `pyproject.toml` package version/extras.
- TypeScript SDK exports, `mem0ai/oss` API, or Node engine constraints.
- CLI `cli/cli-spec.json` command/flag/output contract.
- Self-hosted server auth, Compose services, migration sequence, or dashboard API key behavior.
- OpenMemory MCP/API/UI setup.
- Vercel AI provider API, supported AI SDK major version, or plugin setup instructions.
- Repo-local published skills under `skills/`.
