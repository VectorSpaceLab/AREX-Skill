# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "docling",
    "remote_url": "https://github.com/docling-project/docling.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "898dd7330dc15a8c9d7294df1aea409e74cf396c",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "docling-slim",
      "version": "2.104.0",
      "import_names": ["docling"]
    },
    {
      "name": "docling",
      "version": "2.104.0",
      "import_names": ["docling"]
    }
  ],
  "entry_points": {
    "console_scripts": ["docling", "docling-tools"]
  },
  "evidence": {
    "source_roots": ["docling"],
    "package_metadata": ["pyproject.toml", "packages/docling/pyproject.toml", "packages/docling-slim/README.md", "packages/docling/README.md"],
    "docs": ["README.md", "docs/getting_started", "docs/usage", "docs/concepts", "docs/reference"],
    "examples": ["docs/examples"],
    "tests": ["tests"],
    "scripts": ["scripts"],
    "agent_guidance": ["AGENTS.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current dirty paths differ from `dirty_paths`, inspect whether the changes affect source, docs, examples, packaging, tests, or generated skills.
- If `docling`/`docling-slim` package versions, optional dependency groups, CLI entry points, supported formats, or public APIs changed, refresh the skill even when the commit is unchanged.
- If docling-serve service API docs or service client datamodels changed, refresh `remote-service-client` coverage.
