# LangBot Cross-Cutting Troubleshooting

Read this first when the failure crosses more than one subsystem. Then open the
nearest sub-skill troubleshooting page for workflow-specific symptoms.

## Install or Import Fails

Symptoms include `ModuleNotFoundError: langbot`, missing `langbot --help`, or a
local SDK change disappearing after `uv run`.

Actions:
1. Use `uv sync --dev` for source work or install the package with `pip`/`uv` for
   package-only use.
2. Use Python `>=3.11,<4.0`; prefer 3.11 or 3.12 when compiled wheels matter.
3. After intentionally installing a sibling SDK checkout, run LangBot with
   `uv run --no-sync ...` so the pinned SDK package is not restored.
4. Run the bundled doctor:

```bash
python scripts/langbot_repo_doctor.py --repo-root /path/to/LangBot
```

## Startup Succeeds but Services Are Not Reachable

- Check `/healthz`; it should return `code: 0` and resource stats.
- Confirm `api.port` and generated `data/config.yaml` values.
- If the web UI is missing in a source checkout, build the frontend or use the
  packaged/PyPI path where built frontend assets are included.
- If package downloads or git dependency fetches fail, retry with the local
  network/proxy policy rather than embedding network details in code or skills.

## Authentication Returns 401 or 403

- `401` means no valid user token/API key/global key was accepted.
- `403` means authentication succeeded but the principal lacks the permission.
- `api.global_api_key` is a Community singleton-Workspace bootstrap key; it is
  plaintext and should be trusted/internal only.
- Database-backed API keys are `lbk_...`, shown once, stored as hashes, and
  bound to one Workspace. `X-Workspace-Id` cannot redirect them.

## Optional Services Are Missing

| Optional surface | Required only when | First check |
|---|---|---|
| Docker/Podman | Real Box sandbox, stdio MCP hosting in containers, native tool execution through Box | Box status endpoints and Docker socket permissions |
| PostgreSQL/pgvector | Postgres migrations, cloud/toB database behavior, pgvector backend | service DSN and migration tests |
| Valkey/Qdrant/Milvus/SeekDB | Live vector backend integration | backend-specific config and service reachability |
| Provider/platform credentials | Real LLM calls or live IM adapters | fake/unit tests first |
| Browser/Playwright | Web UI user-path QA | frontend install and browser readiness |

A skipped optional backend is not a pass; record it as skipped/unverified unless
the task explicitly requires it and the environment provides it.

## Cross-Repo SDK Confusion

If a task changes plugin component APIs, message/event entities, action
protocols, `lbp rt`, or `lbp box`, the source of truth is the sibling
`langbot-plugin-sdk` repository. Install that SDK into LangBot's environment and
run LangBot with `--no-sync` during verification.

## Which Sub-Skill Owns the Next Step?

- Boot/config/deploy/health: `core-runtime`.
- API/MCP/Web/auth: `api-mcp-web`.
- Message flow, adapters, pipelines, providers, HTTP Bot: `platform-pipeline-provider`.
- Plugin Runtime, Box, skills, native/MCP stdio tools: `plugin-box-skills`.
- Database, migration, RAG, vector, storage, tenancy, monitoring: `persistence-rag-workspaces`.
- Test selection/evidence: `testing-qa`.
