# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current DataFlow checkout. If the commit, working tree state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T19:36:08Z",
  "repository": {
    "name": "DataFlow",
    "remote_url": "https://github.com/OpenDCAI/DataFlow.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "551873341f07c427601a717bbfc8f200f4ea5e3b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "open-dataflow",
      "version": "1.0.10",
      "import_names": ["dataflow"]
    }
  ],
  "evidence": {
    "source_roots": ["dataflow"],
    "docs": ["README.md", "README-zh.md"],
    "examples": ["dataflow/statics/playground", "dataflow/statics/pipelines"],
    "tests": ["test"],
    "configs": ["pyproject.toml", "requirements.txt", "MANIFEST.in", "pytest.ini", "Dockerfile", ".github/workflows/test.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the dirty-path shape changes materially, or the checkout becomes clean while this snapshot says dirty, refresh it.
- If package metadata or public entry points change, refresh it even if the commit is unchanged.
