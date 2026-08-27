# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of the
`stitching` repository. If the current commit, dirty state, package version,
or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T20:51:51Z",
  "repository": {
    "name": "stitching",
    "remote_url": "https://github.com/lukasalexanderweber/stitching",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f49ffbefccc67596059109b98665d4a891cd3fc0",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "stitching",
      "version": "0.6.1",
      "import_names": ["stitching"]
    }
  ],
  "evidence": {
    "source_roots": ["stitching"],
    "docs": ["README.md", "CONTRIBUTING.md"],
    "examples": [],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.cfg", "requirements.txt", ".github/workflows/python-unittests.yml", "Dockerfile"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, refresh this skill.
- If the working tree becomes dirty or the dirty paths change, refresh this
  skill.
- If package metadata, public entry points, or installed defaults change, or if
  the repo's OpenCV/headless guidance changes, refresh this skill.
