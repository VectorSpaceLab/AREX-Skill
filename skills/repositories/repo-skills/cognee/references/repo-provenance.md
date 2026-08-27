# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Cognee repository. If the current repo commit, dirty state, package version, entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T18:55:00Z",
  "repository": {
    "name": "cognee",
    "remote_url": "https://github.com/topoteretes/cognee.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a148eab58eb2f9769585f10da5486543c9ece457",
    "working_tree": "clean-at-snapshot-before-generated-skill-files",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "cognee",
      "version": "1.4.2",
      "import_names": ["cognee"]
    },
    {
      "name": "cognee-mcp",
      "version": "0.5.5",
      "import_names": ["cognee-mcp entry point", "src package in cognee-mcp distribution"]
    }
  ],
  "evidence": {
    "source_roots": ["cognee", "cognee_db_workers", "distributed", "kuzu", "cognee-mcp/src"],
    "docs": ["README.md", "docs/docker-colima-setup.md", "docs/ollama_models.md", "cognee-mcp/README.md", "cognee-frontend/README.md"],
    "examples": ["examples/README.md", "examples/demos", "examples/guides", "examples/custom_pipelines", "examples/database_examples", "examples/configurations"],
    "tests": ["cognee/tests", "cognee-mcp/tests", "tests"],
    "configs": ["pyproject.toml", "cognee-mcp/pyproject.toml", ".env.template", "docker-compose.yml", "Dockerfile", "cognee-mcp/Dockerfile", "cognee-frontend/package.json"],
    "existing_skills": ["cognee/skill.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If package metadata, public imports, console scripts, or MCP service entry points changed, refresh even on the same commit.
- If a checkout has local modifications in evidence paths, refresh before relying on implementation-specific details.
- Generated skill files under `skills/` are not part of the source baseline used above.
