# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:52:15Z",
  "repository": {
    "name": "flashtext",
    "remote_url": "https://github.com/vi3k6i5/flashtext",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f49274459bc9879789c6e6bb64bf05af755de0b3",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "flashtext",
      "version": "2.7",
      "import_names": ["flashtext"]
    }
  ],
  "evidence": {
    "source_roots": ["flashtext"],
    "docs": ["README.rst", "docs"],
    "examples": [],
    "tests": ["test"],
    "configs": ["setup.py", "setup.cfg", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run
  `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit,
  run `refresh-repo-skill`.
