# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
M-flow repository. If the current repo commit, dirty state, package version, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:56:00Z",
  "repository": {
    "name": "m_flow",
    "remote_url": "https://github.com/FlowElement-xinliuyuansu/m_flow",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0d585cda2f588af69fb872ae6914caba0c217816",
    "working_tree": "clean at source-analysis snapshot before generated skill output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mflow-ai",
      "version": "0.3.6",
      "import_names": ["m_flow"]
    },
    {
      "name": "m_flow-mcp",
      "version": "0.6.0",
      "import_names": ["src"]
    }
  ],
  "entry_points": {
    "console_scripts": ["mflow=m_flow.cli.app:main"]
  },
  "evidence": {
    "source_roots": ["m_flow", "mflow_workers", "m_flow-mcp/src"],
    "docs": ["README.md", "docs/RETRIEVAL_ARCHITECTURE.md", "docs/CUSTOM_LLM_PROVIDERS.md", "m_flow-mcp/README.md"],
    "examples": ["examples"],
    "tests": ["m_flow/tests", "m_flow-mcp/src/test*.py", "m_flow-frontend/src/**/__tests__", "m_flow-frontend/e2e"],
    "configs": ["pyproject.toml", ".env.template", "docker-compose.yml", "m_flow-frontend/package.json", "m_flow-mcp/pyproject.toml"],
    "scripts": ["quickstart.sh", "quickstart.ps1", "scripts/manage_service.sh", "scripts/migrate_created_at.py", "scripts/migrate_lancedb_created_at.py", "scripts/setup-playground.sh"]
  },
  "verification_baseline": {
    "required_backend": "any/cpu",
    "optional_backends_not_claimed": ["neo4j", "postgres", "pgvector", "chromadb", "pinecone", "milvus", "redis", "mcp-service", "frontend-node", "face-recognition", "modal"],
    "private_environment_status": "ok"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, public exports, console entry points, CLI commands,
  supported RecallMode values, or documented environment variables changed, run
  `refresh-repo-skill` even on the same commit.
- If a task depends on an optional backend listed as not claimed, verify that
  backend in the user's current environment before relying on it.
- Generated skill files under `skills/` are output artifacts and were not part
  of the source-analysis snapshot.
