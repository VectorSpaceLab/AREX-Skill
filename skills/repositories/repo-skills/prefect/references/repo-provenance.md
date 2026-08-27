# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Prefect. If the current repo commit, dirty state, package version, public CLI/API routes, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "prefect",
    "remote_url": "https://github.com/prefecthq/prefect",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9c421de26af8e6bda6fa84cc0b3389d96e34e1f7",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "prefect",
      "version": "3.6.24",
      "import_names": ["prefect"]
    },
    {
      "name": "prefect-client",
      "version": "3.6.24",
      "import_names": ["prefect"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/prefect",
      "client"
    ],
    "docs": [
      "README.md",
      "docs/v3",
      "docs/snippets",
      "docs/contribute"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "tests",
      "integration-tests",
      "compat-tests"
    ],
    "configs": [
      "pyproject.toml",
      "client/pyproject.toml",
      "schemas",
      "src/prefect/deployments/templates/prefect.yaml",
      "justfile",
      ".pre-commit-config.yaml"
    ],
    "scripts": [
      "scripts",
      "tools"
    ],
    "excluded_or_shallow": [
      "src/integrations",
      "ui",
      "ui-v2",
      "load_testing",
      "benches"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths include Prefect source, docs, examples, schemas, scripts, tests, package metadata, or configuration paths outside generated `skills/`, run `refresh-repo-skill`.
- If `prefect version`, `prefect --help`, `pyproject.toml`, `client/pyproject.toml`, public decorators, deployment APIs, client/settings APIs, or CLI command help changed, run `refresh-repo-skill` even on the same commit.
- If the task targets deep integration packages or UI implementation, create or route to a dedicated skill for that surface instead of expanding this core Prefect skill ad hoc.
