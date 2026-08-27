# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Recommenders. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:32:32Z",
  "repository": {
    "name": "recommenders",
    "remote_url": "https://github.com/recommenders-team/recommenders.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6232b154548c955315650d58dca6bf1411c56020",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/recommenders/"
    ]
  },
  "packages": [
    {
      "name": "recommenders",
      "version": "1.2.1",
      "import_names": ["recommenders"]
    }
  ],
  "evidence": {
    "source_roots": ["recommenders"],
    "docs": ["README.md", "SETUP.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "tests/test_groups.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the working tree dirty paths differ materially from this snapshot, run `refresh-repo-skill`.
- If package metadata or public entry points change even on the same commit, run `refresh-repo-skill`.
