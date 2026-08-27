# Repository Provenance

Read this before deciding whether this operating skill still matches a
DreamerV2 checkout. If the commit, dirty state, package metadata, or major
evidence paths differ, use `refresh-repo-skill` before relying on detailed
claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:42:07Z",
  "repository": {
    "name": "dreamerv2",
    "remote_url": "https://github.com/danijar/dreamerv2.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "07d906e9c4322c6fc2cd6ed23e247ccd6b7c8c41",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "dreamerv2",
      "version": "2.2.0",
      "import_names": ["dreamerv2", "dreamerv2.api", "dreamerv2.common"]
    }
  ],
  "evidence": {
    "source_roots": ["dreamerv2", "dreamerv2/common"],
    "docs": ["README.md"],
    "examples": ["examples/minigrid.py"],
    "tests": [],
    "configs": ["dreamerv2/configs.yaml", "Dockerfile", "setup.py"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- If the current working tree is clean or its changed paths differ, refresh;
  this generation intentionally records the repository as dirty because the
  generated skill and review artifacts live below `skills/`.
- Recheck package entry points, `configs.yaml`, TensorFlow compatibility, and
  environment adapter APIs if the package metadata or source roots change.
- The source snapshot has no repository-owned test suite; native candidates are
  safe help checks and tiny API/config fixtures rather than benchmark results.
