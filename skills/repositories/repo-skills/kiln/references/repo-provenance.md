# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Kiln. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:59:33Z",
  "repository": {
    "name": "Kiln",
    "remote_url": "https://github.com/Kiln-AI/Kiln.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7b70de19830462573b7cad153f6411f3422ef4f8",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "kiln-ai", "version": "1.0.4", "import_names": ["kiln_ai"], "entry_points": ["kiln_ai"]},
    {"name": "kiln-server", "version": "1.0.4", "import_names": ["kiln_server"], "entry_points": ["kiln_server", "kiln_mcp"]},
    {"name": "kiln-studio-desktop", "version": "1.0.4", "import_names": ["app.desktop when used from a checkout"]}
  ],
  "evidence": {
    "source_roots": ["libs/core/kiln_ai", "libs/server/kiln_server", "app/desktop", "app/web_ui/src"],
    "docs": ["README.md", "libs/core/README.md", "libs/server/README.md", "libs/server/kiln_server/mcp/README.md", "app/desktop/README.md", "specs/monorepo.md", ".agents/*.md"],
    "examples": ["libs/core/README.md code examples", "libs/core/tests/assets"],
    "tests": ["libs/core/kiln_ai/**/test_*.py", "libs/server/kiln_server/test_*.py", "app/desktop/studio_server/test_*.py", "app/desktop/git_sync/test_*.py", "app/web_ui/src/**/*.test.ts", "app/web_ui/tests/e2e/*.spec.ts"],
    "configs": ["pyproject.toml", "libs/core/pyproject.toml", "libs/server/pyproject.toml", "app/desktop/pyproject.toml", "app/web_ui/package.json", "uv.lock"],
    "scripts": ["checks.sh", "app/web_ui/src/lib/check_schema.sh", "app/web_ui/src/lib/generate_schema.sh", "app/desktop/run_desktop_dev.sh", "app/desktop/build_desktop_app.sh"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current dirty state differs from the snapshot, especially outside generated skills/artifacts, refresh before relying on fine API details.
- If package versions, CLI entry points, FastAPI route assembly, OpenAPI schema scripts, or public datamodel fields changed, refresh.
- If dependency resolution changes import behavior for `mcp`, `starlette`, LanceDB/RAG, or desktop/studio-server imports, refresh the troubleshooting notes.
