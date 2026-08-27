# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an Open Wearables checkout. If the current repo commit, package metadata, provider inventory, route map, frontend scripts, or MCP tool surface differs from this snapshot, run `refresh-repo-skill` rather than patching the generated skill manually.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:16:01Z",
  "repository": {
    "name": "open-wearables",
    "remote_url": "https://github.com/the-momentum/open-wearables.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b16e9fd58ce74a7b874c65e40ea91b95836cea26",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "open-wearables",
      "version": "0.7.0",
      "import_names": ["app"],
      "role": "backend"
    },
    {
      "name": "frontend-app",
      "version": "0.7.0",
      "import_names": [],
      "role": "frontend"
    },
    {
      "name": "open-wearables-mcp",
      "version": "0.1.0",
      "import_names": ["app"],
      "role": "mcp"
    }
  ],
  "evidence": {
    "source_roots": [
      "backend/app",
      "frontend/src",
      "mcp/app"
    ],
    "metadata": [
      "backend/pyproject.toml",
      "frontend/package.json",
      "mcp/pyproject.toml",
      "docker-compose.yml",
      "Makefile"
    ],
    "docs": [
      "README.md",
      "AGENTS.md",
      "backend/AGENTS.md",
      "frontend/AGENTS.md",
      "backend/README.md",
      "frontend/README.md",
      "mcp/README.md",
      "docs/architecture",
      "docs/dev-guides",
      "docs/providers",
      "docs/mcp-server",
      "docs/docs.json"
    ],
    "tests": [
      "backend/tests",
      "frontend/src/lib/utils/activity.test.ts",
      "frontend/src/lib/utils/format.test.ts",
      "mcp/tests"
    ],
    "scripts": [
      "backend/scripts/generate_coverage_docs.py",
      "backend/scripts/healthchecks/db_up_check.py",
      "backend/scripts/init",
      "backend/scripts/start"
    ],
    "excluded_or_reference_only": [
      "frontend/src/routeTree.gen.ts",
      "backend/scripts/reset_database.py",
      "backend/scripts/replay_raw_payloads.py",
      "backend/scripts/data_migrations",
      "build/cache/node_modules/venv artifacts"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If package versions, Python/Node requirements, console scripts, provider count, frontend package scripts, or MCP tool names changed, refresh the skill.
- If route tags or `External: *` endpoint placement changed, refresh and re-run API Reference navigation checks.
- If provider coverage constants or the coverage docs generator changed, refresh the `provider-integrations` sub-skill.
- If a checkout is dirty before skill-generation artifacts are considered, review the dirty paths and prefer `refresh-repo-skill` with a clear source snapshot.

The snapshot above was captured before generated skill and construction artifacts were written; those generated artifacts are not part of the source baseline.
