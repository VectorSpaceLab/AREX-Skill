# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Rasterio. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run a refresh pass.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:24:43Z",
  "repository": {
    "name": "rasterio",
    "remote_url": "https://github.com/rasterio/rasterio.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9709d1fce53b8c11ace1741ef25cfe427b197fb8",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "rasterio",
      "version": "1.5.1",
      "import_names": ["rasterio"]
    }
  ],
  "evidence": {
    "source_roots": ["rasterio"],
    "docs": ["README.rst", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat the skill as potentially stale and refresh it.
- If the selected public package version changes, or the CLI/API surface shifts, refresh it.
- If the included evidence paths change substantially, refresh it.
