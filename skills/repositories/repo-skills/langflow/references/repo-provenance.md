# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Langflow. If the current repo commit, dirty state, package versions, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-30T00:00:00Z",
  "repository": {
    "name": "langflow",
    "remote_url": "https://github.com/langflow-ai/langflow.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7db38d1abbdc9ae764f8e7e28da64cb5104217f6",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "langflow", "version": "1.10.1", "import_names": ["langflow"]},
    {"name": "langflow-base", "version": "0.10.1", "import_names": ["langflow"]},
    {"name": "lfx", "version": "1.10.1", "import_names": ["lfx"]},
    {"name": "langflow-sdk", "version": "0.2.1", "import_names": ["langflow_sdk"]},
    {"name": "lfx-arxiv", "version": "0.1.1", "import_names": ["lfx_arxiv"]},
    {"name": "lfx-docling", "version": "0.1.1", "import_names": ["lfx_docling"]},
    {"name": "lfx-duckduckgo", "version": "0.1.1", "import_names": ["lfx_duckduckgo"]},
    {"name": "lfx-ibm", "version": "0.1.1", "import_names": ["lfx_ibm"]}
  ],
  "evidence": {
    "source_roots": [
      "src/backend/base/langflow",
      "src/backend/langflow",
      "src/lfx/src/lfx",
      "src/sdk/src/langflow_sdk",
      "src/bundles/arxiv/src/lfx_arxiv",
      "src/bundles/docling/src/lfx_docling",
      "src/bundles/duckduckgo/src/lfx_duckduckgo",
      "src/bundles/ibm/src/lfx_ibm",
      "src/frontend/src"
    ],
    "docs": [
      "README.md",
      "DEVELOPMENT.md",
      "CONTRIBUTING.md",
      "AGENTS.md",
      "docs/docs",
      "docs/agents",
      "src/lfx/README.md",
      "src/sdk/README.md",
      "deploy/README.md",
      "docker_example/README.md"
    ],
    "examples": [
      "src/backend/base/langflow/initial_setup/starter_projects",
      "docker_example",
      "deploy"
    ],
    "tests": [
      "src/backend/tests",
      "src/lfx/tests",
      "src/sdk/tests",
      "src/frontend/tests",
      "src/bundles/*/tests"
    ],
    "configs": [
      "pyproject.toml",
      "src/backend/base/pyproject.toml",
      "src/lfx/pyproject.toml",
      "src/sdk/pyproject.toml",
      "src/frontend/package.json",
      "src/bundles/*/pyproject.toml",
      "docker_example/docker-compose.yml",
      "deploy/docker-compose.yml"
    ],
    "scripts": [
      "scripts/build_component_index.py",
      "scripts/generate_migration.py",
      "scripts/migrate_secret_key.py",
      "scripts/test-api-examples-local.sh",
      "docs/openapi/generate_openapi.py",
      "scripts/check_deprecated_imports.py",
      "scripts/migrate",
      "scripts/setup",
      "scripts/ci"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has non-skill dirty paths or differs materially from the recorded dirty path summary, run `refresh-repo-skill`.
- If `langflow`, `langflow-base`, `lfx`, `langflow-sdk`, or bundle versions change, run `refresh-repo-skill`.
- If CLI command groups, API route shapes, component/base classes, SDK models, frontend package scripts, Docker examples, or authorization/database behavior changed, run `refresh-repo-skill` even on the same commit.
