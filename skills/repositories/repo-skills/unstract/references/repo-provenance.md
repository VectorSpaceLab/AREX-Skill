# Repository Provenance

Read this before deciding whether the generated `unstract` skill still matches a checkout of this repository. If the current commit, dirty state, package versions, or major evidence paths differ materially from this snapshot, refresh the skill.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T20:08:46Z",
  "repository": {
    "name": "unstract",
    "remote_url": "https://github.com/Zipstack/unstract.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "90415861699ab2baf6b4e538257bed501b39c317",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "workspace": {
    "name": "unstract",
    "version": "0.1.0",
    "requires_python": ">=3.12,<3.13"
  },
  "packages": [
    {
      "name": "unstract-sdk1",
      "version": "1.0.0",
      "import_names": ["unstract.sdk1"],
      "entry_points": []
    },
    {
      "name": "unstract-core",
      "version": "0.0.1",
      "import_names": ["unstract.core"],
      "entry_points": []
    },
    {
      "name": "unstract-connectors",
      "version": "0.0.3",
      "import_names": ["unstract.connectors"],
      "entry_points": []
    },
    {
      "name": "unstract-filesystem",
      "version": "0.0.1",
      "import_names": ["unstract.filesystem"],
      "entry_points": []
    },
    {
      "name": "unstract-flags",
      "version": "0.0.1",
      "import_names": ["unstract.flags"],
      "entry_points": []
    },
    {
      "name": "unstract-tool-registry",
      "version": "0.0.1",
      "import_names": ["unstract.tool_registry"],
      "entry_points": []
    },
    {
      "name": "unstract-tool-sandbox",
      "version": "0.0.1",
      "import_names": ["unstract.tool_sandbox"],
      "entry_points": []
    },
    {
      "name": "unstract-workflow-execution",
      "version": "0.0.1",
      "import_names": ["unstract.workflow_execution"],
      "entry_points": []
    }
  ],
  "evidence": {
    "source_roots": [
      "backend/backend",
      "backend/account_v2",
      "backend/api_v2",
      "backend/file_management",
      "backend/mcp_server",
      "backend/pipeline_v2",
      "backend/platform_api",
      "platform-service/src/unstract/platform_service",
      "runner",
      "tool-sidecar",
      "x2text-service/app",
      "frontend/src",
      "unstract/connectors/src",
      "unstract/core/src",
      "unstract/filesystem/src",
      "unstract/flags/src",
      "unstract/sdk1/src",
      "unstract/tool-registry/src",
      "unstract/tool-sandbox/src",
      "unstract/workflow-execution/src",
      "workers",
      "tools",
      "tests/rig",
      "tests/e2e",
      "tests/integration"
    ],
    "docs": [
      "README.md",
      "backend/README.md",
      "backend/mcp_server/README.md",
      "docs/ARCHITECTURE.md",
      "frontend/README.md",
      "platform-service/README.md",
      "runner/README.md",
      "tool-sidecar/README.md",
      "tools/README.md",
      "tools/classifier/README.md",
      "tools/text_extractor/README.md",
      "tests/README.md",
      "unstract/connectors/README.md",
      "unstract/core/README.md",
      "unstract/filesystem/README.md",
      "unstract/flags/README.md",
      "unstract/sdk1/README.md",
      "unstract/tool-registry/README.md",
      "unstract/tool-sandbox/README.md",
      "unstract/workflow-execution/README.md",
      "workers/ARCHITECTURE.md",
      "workers/OPERATIONS.md",
      "workers/README.md",
      "x2text-service/README.md"
    ],
    "package_metadata": [
      "pyproject.toml",
      "backend/pyproject.toml",
      "frontend/package.json",
      "platform-service/pyproject.toml",
      "runner/pyproject.toml",
      "tool-sidecar/pyproject.toml",
      "workers/pyproject.toml",
      "x2text-service/pyproject.toml",
      "unstract/connectors/pyproject.toml",
      "unstract/core/pyproject.toml",
      "unstract/filesystem/pyproject.toml",
      "unstract/flags/pyproject.toml",
      "unstract/sdk1/pyproject.toml",
      "unstract/tool-registry/pyproject.toml",
      "unstract/tool-sandbox/pyproject.toml",
      "unstract/workflow-execution/pyproject.toml"
    ],
    "tests": [
      "backend/mcp_server/tests",
      "backend/tests_common",
      "platform-service/tests",
      "tests/e2e",
      "tests/integration",
      "tests/rig",
      "unstract/connectors/tests",
      "unstract/core/tests",
      "unstract/sdk1/tests",
      "unstract/tool-registry/tests",
      "workers/shared/tests",
      "workers/tests"
    ],
    "deployment": [
      "backend/entrypoint.sh",
      "frontend/generate-runtime-config.sh",
      "run-platform.sh",
      "runner/entrypoint.sh",
      "tool-sidecar/entrypoint.sh",
      "unstract/tool-registry/scripts/load_tools_to_json.py",
      "workers/run-worker-docker.sh",
      "workers/run-worker.sh",
      "x2text-service/run.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as stale and refresh it.
- If the working tree becomes dirty, record the changed relative paths in a refreshed provenance snapshot.
- If public package versions, console entry points, route families, hosted MCP behavior, or worker/service startup contracts change, refresh the skill.
- If new user-facing services, packages, tools, or tests are added, refresh or extend the skill depending on whether the existing coverage is still structurally adequate.
