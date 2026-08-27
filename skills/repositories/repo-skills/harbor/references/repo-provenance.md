# Repository Provenance

Read this before deciding whether this Harbor operating graph matches the
source version. If the commit, package metadata, public entrypoints, or major
evidence paths differ, run `refresh-repo-skill` before relying on version-
sensitive guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-23T07:30:00Z",
  "repository": {
    "name": "harbor",
    "remote_url": "https://github.com/harbor-framework/harbor",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b37833221e27435a18d7acdd41d875cdc2831893",
    "working_tree": "dirty",
    "dirty_paths": ["skills/disco/harbor/"]
  },
  "packages": [
    {
      "name": "harbor",
      "version": "0.22.0",
      "import_names": ["harbor"]
    },
    {
      "name": "harbor-rewardkit",
      "version": "0.2.0",
      "import_names": ["rewardkit"]
    },
    {
      "name": "harbor-langsmith",
      "version": "0.3.1",
      "import_names": ["harbor_langsmith"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/harbor",
      "packages/rewardkit/src/rewardkit",
      "packages/harbor-langsmith/src/harbor_langsmith"
    ],
    "docs": [
      "README.md",
      "docs/content/docs/core-concepts.mdx",
      "docs/content/docs/run-jobs",
      "docs/content/docs/tasks",
      "docs/content/docs/datasets",
      "docs/content/docs/agents",
      "docs/content/docs/rewardkit",
      "docs/content/docs/hub",
      "docs/content/docs/sharing"
    ],
    "examples": ["examples/configs", "examples/exec", "examples/tasks", "examples/jobs", "examples/agents", "examples/metrics"],
    "tests": ["tests/unit", "packages/rewardkit/tests", "packages/harbor-langsmith/tests"],
    "configs": ["pyproject.toml", "uv.lock", "registry.json"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- If the working tree is dirty, compare the changed paths with the snapshot;
  this generated graph includes only its own generated skill and review
  artifacts as intentional local changes.
- Recheck `pyproject.toml` for Python floor, Harbor console scripts, optional
  extras, and workspace packages.
- Recheck `AgentName`, `EnvironmentType`, `TaskConfig`, `JobConfig`,
  `TrialConfig`, and `ExecConfig` when a new release changes their fields or
  defaults.
