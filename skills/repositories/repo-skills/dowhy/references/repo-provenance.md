# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:13:22Z",
  "repository": {
    "name": "dowhy",
    "remote_url": "https://github.com/py-why/dowhy.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1d1efe77b092661252038baad72dc5d53e35ebfa",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "dowhy",
      "version": "0.0.0",
      "import_names": ["dowhy"]
    }
  ],
  "evidence": {
    "source_roots": ["dowhy"],
    "docs": ["README.rst", "docs/source"],
    "examples": ["example_parallel_refutation.py", "docs/source/example_notebooks"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", ".flake8"]
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
