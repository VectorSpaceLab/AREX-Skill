# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:35:44Z",
  "repository": {
    "name": "MineContext",
    "remote_url": "https://github.com/volcengine/MineContext",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "171c7a9ea8091e326ddcf0f10718aa1b58c83c65",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "MineContext",
      "version": "0.1.0",
      "import_names": ["opencontext"],
      "console_scripts": ["opencontext"]
    },
    {
      "name": "frontend package",
      "version": "0.1.5",
      "import_names": [],
      "console_scripts": ["pnpm dev", "pnpm build:mac", "pnpm build:win", "pnpm build:linux"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "package.json", "frontend/package.json"],
    "source_roots": ["opencontext/", "frontend/src/"],
    "docs": ["README.md", "README_zh.md", "CONTRIBUTING.md", "SECURITY.md", "src/architecture-overview.md", "src/architecture-overview-zh.md"],
    "examples": ["examples/"],
    "tests": [],
    "configs": ["config/config.yaml", "config/prompts_en.yaml", "config/prompts_zh.yaml", "config/quick_start_default.md"],
    "build_and_packaging": ["build.sh", "build.bat", "opencontext.spec", "hook-opencontext.py", "frontend/electron-builder.yml", "frontend/build-python.js", "frontend/build-python.sh", "frontend/start-dev.sh", "frontend/scripts/copy-prebuilt-backend.js", "frontend/externals/python/window_capture/", "frontend/externals/python/window_inspector/"]
  },
  "verified_runtime": {
    "python": "3.11",
    "distribution_metadata": "MineContext 0.1.0",
    "imports": ["opencontext", "opencontext.cli", "opencontext.context_processing.processor.document_processor", "opencontext.storage.backends.chromadb_backend", "opencontext.storage.backends.qdrant_backend", "opencontext.context_capture.screenshot", "opencontext.context_capture.web_link_capture", "opencontext.context_consumption.context_agent.agent"],
    "cli_smoke": "opencontext --help"
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If the current checkout is clean but the snapshot was dirty, or if dirty paths
  differ beyond generated `skills/` output, refresh before relying on exact
  build or API details.
- If package metadata, console entry points, route groups, config keys, or
  frontend build scripts changed even on the same commit, refresh this skill.
- If a future release changes the public package from `MineContext` or the
  import package from `opencontext`, refresh before using any API or CLI
  guidance.
