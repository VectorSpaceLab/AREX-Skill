# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T23:10:04Z",
  "repository": {
    "name": "scikit-plot",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "2dd3e6a76df77edcbd724c4db25575f70abb57cb",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "scikit-plot",
      "version": "0.3.7",
      "import_names": ["scikitplot"]
    }
  ],
  "evidence": {
    "source_roots": ["scikitplot"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["scikitplot/tests"],
    "configs": ["setup.py", "requirements.txt", "environment.yml", "MANIFEST.in"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public module names, or plot function signatures changed, refresh the skill even when the commit appears familiar.
- If the checkout is dirty for reasons other than generated skill/test artifacts, inspect the changed relative paths before trusting this skill.
