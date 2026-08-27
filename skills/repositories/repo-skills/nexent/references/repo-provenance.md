# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Nexent. If the current commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:41:16Z",
  "repository": {
    "name": "nexent",
    "remote_url": "https://github.com/ModelEngine-Group/nexent.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "9c58d9787355197d17d92485f980c8f8c8b3892c",
    "working_tree": "clean-before-generated-skill-artifacts",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "nexent",
      "version": "0.1.2",
      "import_names": ["nexent"]
    },
    {
      "name": "backend",
      "version": "0.1.0",
      "import_names": ["apps", "services", "consts", "database", "agents"]
    },
    {
      "name": "frontend",
      "version": "0.1.0",
      "import_names": []
    },
    {
      "name": "application-version",
      "version": "v2.4.0",
      "import_names": []
    }
  ],
  "evidence": {
    "source_roots": [
      "sdk/nexent",
      "backend/apps",
      "backend/services",
      "backend/database",
      "backend/agents",
      "backend/data_process",
      "backend/consts",
      "frontend/app",
      "frontend/services",
      "frontend/types",
      "deploy"
    ],
    "docs": [
      "README.md",
      "doc/docs/en/sdk",
      "doc/docs/en/backend",
      "doc/docs/en/frontend",
      "doc/docs/en/developer-guide",
      "doc/docs/en/quick-start"
    ],
    "tests": [
      "test/backend",
      "test/sdk",
      "deploy/tests",
      "test/run_all_test.py"
    ],
    "configs": [
      "sdk/pyproject.toml",
      "backend/pyproject.toml",
      "frontend/package.json",
      "deploy/env/.env.example",
      "deploy/sql",
      "VERSION",
      "AGENTS.md"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package metadata, route families, deployment layout, or public API signatures changed, refresh even on the same commit.
- Generated skill artifacts under `skills/` are not source evidence for this provenance baseline.
