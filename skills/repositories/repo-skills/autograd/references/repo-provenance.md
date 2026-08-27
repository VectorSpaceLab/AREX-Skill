# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Autograd. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T18:32:33Z",
  "repository": {
    "name": "autograd",
    "remote_url": "https://github.com/HIPS/autograd.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d94403fbba62953e81599ad76b4ac2c303426bc0",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "autograd",
      "version": "1.9.1",
      "import_names": ["autograd"]
    }
  ],
  "evidence": {
    "source_roots": ["autograd"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "noxfile.py", ".github/workflows"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale and refresh it.
- If the dirty path set changes materially, refresh it.
- If package metadata, public imports, or selected workflow evidence change, refresh it.
