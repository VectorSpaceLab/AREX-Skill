# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Galaxy. If the current repo commit, dirty state, package version, public APIs, client commands, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T00:00:00Z",
  "repository": {
    "name": "galaxy",
    "remote_url": "https://github.com/galaxyproject/galaxy.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "ed7a5aa31bed8b30ff487d8b34abf4ba01045fe5",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "galaxy",
      "version": "26.2.dev0",
      "import_names": ["galaxy"]
    },
    {
      "name": "galaxy-util",
      "version": "26.1.dev0",
      "import_names": ["galaxy.util"]
    },
    {
      "name": "galaxy-config",
      "version": "26.1.dev0",
      "import_names": ["galaxy.config"]
    },
    {
      "name": "galaxy-schema",
      "version": "26.1.dev0",
      "import_names": ["galaxy.schema"]
    },
    {
      "name": "galaxy-tool-util",
      "version": "26.1.dev0",
      "import_names": ["galaxy.tool_util"]
    }
  ],
  "evidence": {
    "source_roots": [
      "lib/galaxy",
      "lib/tool_shed",
      "lib/tool_shed_client",
      "packages/*/src",
      "client/src",
      "client/packages"
    ],
    "docs": [
      "README.rst",
      "packages/README.md",
      "doc/source/admin",
      "doc/source/api",
      "doc/source/dev",
      "client/README.md"
    ],
    "examples_and_scripts": [
      "scripts/api",
      "scripts/tool_shed",
      "scripts/config_parse.py",
      "scripts/config_sample_to_kwalify.py",
      "scripts/dump_openapi_schema.py",
      "scripts/validate_tools.sh",
      "scripts/objectstore",
      "scripts/cleanup_datasets"
    ],
    "tests": [
      "test/unit",
      "test/integration",
      "test/functional",
      "lib/galaxy_test/api",
      "lib/galaxy_test/workflow",
      "packages/*/tests",
      "client/tests",
      "client/src/**/*.test.*"
    ],
    "configs": [
      "pyproject.toml",
      "requirements.txt",
      "pytest.ini",
      "tox.ini",
      "config/*.sample",
      "client/package.json",
      "client/pnpm-workspace.yaml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current dirty paths include source, docs, package metadata, client commands, tests, configs, or scripts beyond generated skill artifacts, run `refresh-repo-skill`.
- If `galaxy.version.VERSION`, split package versions, public API routes, tool-util CLIs, config schema behavior, Tool Shed metadata workflows, or client package scripts changed, run `refresh-repo-skill`.
- If the active checkout lacks evidence paths used above, run `refresh-repo-skill` before relying on detailed guidance.
