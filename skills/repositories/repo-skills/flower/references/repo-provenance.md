# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current Flower
checkout. If the commit, dirty state, package version, or major evidence paths
change, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T19:05:47Z",
  "repository": {
    "name": "flower",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "69cdb6771acd889375ebe0172f71a74a4b55c7ed",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "flwr",
      "version": "1.34.0",
      "import_names": ["flwr"]
    },
    {
      "name": "flwr-datasets",
      "version": "0.6.0",
      "import_names": ["flwr_datasets"]
    }
  ],
  "evidence": {
    "source_roots": [
      "framework/py/flwr",
      "datasets/flwr_datasets"
    ],
    "docs": [
      "README.md",
      "framework/docs/source",
      "datasets/docs/source"
    ],
    "examples": ["examples"],
    "tests": [
      "framework/py/flwr/**/*_test.py",
      "datasets/flwr_datasets/**/*_test.py",
      "framework/e2e",
      "examples/*/pyproject.toml"
    ],
    "configs": [
      "framework/pyproject.toml",
      "datasets/pyproject.toml",
      "AGENTS.md",
      "framework/AGENTS.md"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, the skill is stale.
- If the working tree becomes dirty, compare the changed paths with the evidence
  above before trusting the skill.
- If package metadata or entry points change, refresh the skill even when the
  commit stays the same.
