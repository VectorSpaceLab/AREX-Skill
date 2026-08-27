# Repository Provenance

Read this before deciding whether the Mellea operating skill matches a
checkout. If the commit, package version, dirty state, or major evidence paths
differ, run a refresh rather than assuming API compatibility.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "mellea",
    "remote_url": "https://github.com/generative-computing/mellea",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "058e3ddc5cba0782ef1b85e2b3e37fb200a600e0",
    "working_tree": "dirty",
    "dirty_paths": ["generated skill and review artifacts outside the source snapshot"]
  },
  "packages": [
    {
      "name": "mellea",
      "version": "0.8.0.dev0",
      "import_names": ["mellea", "cli"]
    }
  ],
  "evidence": {
    "source_roots": ["mellea", "cli"],
    "docs": ["README.md", "docs/docs", "docs/AGENTS_TEMPLATE.md", "AGENTS.md"],
    "examples": ["docs/examples"],
    "tests": ["test"],
    "configs": ["pyproject.toml", "uv.lock", "conda/environment.yml", "test/conftest.py"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare the current package metadata and public entry point with the package
  and `m` entry point recorded above.
- A dirty source tree or changed evidence paths means the commit alone is not a
  sufficient refresh baseline. The generated runtime content itself is
  self-contained; the paths above are provenance only, not runtime dependencies.
