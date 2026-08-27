# Repository Provenance

Read this before deciding whether the generated guidance matches a checkout of
`gget`. If the commit, dirty state, package version, public entry points, or
major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T02:00:00Z",
  "repository": {
    "name": "gget",
    "remote_url": "https://github.com/scverse/gget.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8006088f831b145b95f13b5cdb4823ad95cb740b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/gget.log", "skills/disco/gget/"]
  },
  "packages": [
    {
      "name": "gget",
      "version": "0.30.8",
      "import_names": ["gget"]
    }
  ],
  "evidence": {
    "source_roots": ["gget"],
    "docs": ["README.md", "docs/src/en"],
    "examples": ["README.md", "docs/src/en/quick_start_guide.md"],
    "tests": ["tests", "tests/fixtures"],
    "configs": ["pyproject.toml"]
  }
}
```

The generated skill was produced from a dirty checkout because the repository
already contained `skills/gget.log` and the generated output is intentionally
placed under `skills/disco/gget/`. The source commit and package metadata remain
the refresh baseline; generated review artifacts are not runtime dependencies.

## Refresh check

- Compare `git rev-parse HEAD` with the commit above.
- Compare the current package version and `gget` console entry point with
  `pyproject.toml` and `gget/__init__.py`.
- Check whether public modules, English docs, or the test/fixture layout changed.
- If any of those differ materially, run `refresh-repo-skill` rather than
  patching only a single reference.

External databases and APIs are not version-pinned by this skill. Revalidate
remote schemas and current service behavior at execution time.
