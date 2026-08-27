# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an Onyx checkout. If the current commit, dirty state, package metadata, or major evidence paths differ materially from this snapshot, run `refresh-repo-skill` before relying on the generated graph for detailed guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T14:35:00Z",
  "repository": {
    "name": "onyx",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": "nightly-latest-20260808",
    "commit": "5200dade0709f926f15309dbe48b1e43e680c202",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "onyx",
      "version": "0.0.0",
      "import_names": ["onyx"],
      "notes": "Root pyproject sets tool.uv.package=false; backend imports are source/PYTHONPATH based."
    },
    {
      "name": "web",
      "version": "1.0.0-dev",
      "import_names": []
    },
    {
      "name": "mobile",
      "version": "1.0.0",
      "import_names": []
    },
    {
      "name": "onyx-cli",
      "version": null,
      "import_names": [],
      "notes": "Dynamic version from cli tag metadata."
    },
    {
      "name": "onyx-devtools",
      "version": null,
      "import_names": [],
      "notes": "Dynamic version from ods tag metadata; root dependencies pin published onyx-devtools 0.10.6."
    }
  ],
  "evidence": {
    "source_roots": [
      "backend/onyx",
      "backend/ee/onyx",
      "backend/model_server",
      "web/src",
      "web/lib/opal",
      "web/lib/shared",
      "mobile/src",
      "cli",
      "tools/ods"
    ],
    "docs": [
      "README.md",
      "CONTRIBUTING.md",
      "AGENTS.md",
      "backend/AGENTS.md",
      "web/AGENTS.md",
      "mobile/AGENTS.md",
      "backend/onyx/background/README.md",
      "backend/onyx/chat/README.md",
      "backend/onyx/connectors/README.md",
      "backend/onyx/document_index/opensearch/README.md",
      "backend/onyx/file_store/README.md",
      "backend/onyx/mcp_server/README.md",
      "backend/tests/README.md",
      "backend/tests/integration/README.md",
      "web/README.md",
      "web/tests/README.md",
      "web/tests/e2e/README.md",
      "web/lib/opal/README.md",
      "mobile/README.md",
      "docs/craft",
      "docs/mobile-chat",
      "cli/README.md",
      "tools/ods/README.md",
      "deployment/docker_compose/README.md"
    ],
    "tests": [
      "backend/tests/unit",
      "backend/tests/external_dependency_unit",
      "backend/tests/integration",
      "web/tests",
      "web/src/**/*.test.ts*",
      "mobile/src/**/*.test.ts*",
      "cli/**/*_test.go",
      "tools/ods/**/*_test.go"
    ],
    "configs": [
      "pyproject.toml",
      "uv.lock",
      "package.json",
      "web/package.json",
      "mobile/package.json",
      "cli/pyproject.toml",
      "tools/ods/pyproject.toml",
      "deployment/docker_compose",
      "deployment/helm"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If source directories, dependency groups, front-end package versions, CLI command surfaces, or deployment templates changed materially, refresh the skill even on the same commit.
- Ignore the generated `skills/` output itself when comparing the original source baseline; it is recorded as dirty because this skill was generated inside the repository checkout.
- If a future task centers on lower-depth areas such as load testing, widget/extensions, or model-server accelerator runtime, extend or refresh the graph with targeted evidence before relying on this snapshot.
