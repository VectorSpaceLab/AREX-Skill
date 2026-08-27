# Repository Provenance

## Purpose

Read this before deciding whether the `apod-api` operating skill still matches
a checkout of the public repository. If the commit, dirty state, package
version, or public evidence paths differ, run a repository-skill refresh before
relying on exact route or parser behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:39:51Z",
  "repository": {
    "name": "apod-api",
    "remote_url": "https://github.com/nasa/apod-api.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "fcead2860c7f2ae43c09e4d0c8c4c34345d789fc",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "apod-api",
      "version": "1.1.0",
      "import_names": ["application", "apod", "apod_parser"]
    }
  ],
  "evidence": {
    "source_roots": ["application.py", "apod", "apod_parser"],
    "docs": ["README.md", "apod_parser/apod_parser_readme.md"],
    "examples": [],
    "tests": ["tests/apod", "tests/load"],
    "configs": ["pyproject.toml", "uv.lock", "Dockerfile", "docker-compose.yml", "templates", "static"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and refresh it.
- If the current working tree is clean, or its changed paths differ materially
  from this snapshot, refresh it. The generated skill and review artifacts are
  intentionally under `skills/` and explain the dirty state recorded above.
- If package metadata, route definitions, parser exports, deployment files, or
  query fields change even on the same commit, refresh it.

The snapshot records only relative evidence paths and public package facts. It
does not encode a local Python executable, environment prefix, checkout path,
credential, or private cache.
