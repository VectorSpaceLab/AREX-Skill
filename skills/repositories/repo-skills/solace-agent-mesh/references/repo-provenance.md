# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Solace Agent Mesh. If the current commit, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on detailed instructions.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:09:21Z",
  "repository": {
    "name": "solace-agent-mesh",
    "remote_url": "https://github.com/SolaceLabs/solace-agent-mesh.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2b4ef6ab54e796bc77f12d5edb84dbb656e36610",
    "working_tree": "source-clean-with-generated-skill-output",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "solace-agent-mesh",
      "version": "1.28.7",
      "import_names": ["solace_agent_mesh"]
    },
    {
      "name": "sam-rest-client",
      "version": "0.1.0",
      "import_names": ["sam_rest_client"]
    }
  ],
  "entry_points": {
    "console_scripts": [
      "sam = solace_agent_mesh.cli.main:cli",
      "solace-agent-mesh = solace_agent_mesh.cli.main:cli",
      "sam-rest-cli = sam_rest_client.cli:main"
    ]
  },
  "evidence": {
    "source_roots": [
      "cli/",
      "src/solace_agent_mesh/",
      "evaluation/",
      "config_portal/backend/",
      "client/sam-rest-client/src/sam_rest_client/"
    ],
    "docs": [
      "README.md",
      "docs/docs/documentation/components/",
      "docs/docs/documentation/developing/",
      "docs/docs/documentation/installing-and-configuring/"
    ],
    "examples": ["examples/", "tests/evaluation/"],
    "tests": [
      "tests/unit/cli/",
      "tests/unit/workflow/",
      "tests/integration/gateway/",
      "tests/integration/apis/",
      "tests/integration/scenarios_programmatic/"
    ],
    "templates": ["templates/"],
    "configs": ["config_portal/backend/", "templates/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If public package metadata, console script names, or command help differs, refresh even when the commit is unchanged.
- The snapshot was taken after writing generated skill files under `skills/`; do not treat those files alone as source drift. Source-code or documentation changes outside generated skill artifacts are refresh signals.
- If current evidence paths are missing or substantially reorganized, refresh before using detailed sub-skill instructions.
