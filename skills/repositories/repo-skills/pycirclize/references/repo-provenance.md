# Repository Provenance

Read this before deciding whether the pyCirclize skill is current for a
checkout. If the commit, package version, dirty state, or major evidence paths
differ, run a refresh workflow before relying on detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T09:00:00Z",
  "repository": {
    "name": "pyCirclize",
    "remote_url": "https://github.com/moshi4/pyCirclize/",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5a0f36111a4bbfab3e3d765e7365a1108f891dcb",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pyCirclize",
      "version": "1.10.1",
      "import_names": ["pycirclize"]
    }
  ],
  "evidence": {
    "source_roots": ["src/pycirclize"],
    "docs": ["README.md", "docs", "pyproject.toml"],
    "examples": ["README.md", "docs/*.ipynb"],
    "tests": ["tests", "tests/testdata"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill
  as potentially stale.
- If the current working tree is dirty, or changed dirty paths differ from the
  snapshot, refresh before using version-sensitive details.
- Refresh if public parser exports, Circos factory signatures, coordinate
  conventions, optional tooltip behavior, or runtime dependencies change.
- The evidence baseline intentionally excludes CI/release files, resolver
  locks, generated images, and review artifacts.
