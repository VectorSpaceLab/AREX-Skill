# Repository Provenance

## Purpose

Read this before deciding whether the operating skill still matches a checkout
of `h3-py`. If the source commit, dirty state, package version, submodule, or
major evidence paths differ, run a repository-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T20:31:38Z",
  "repository": {
    "name": "h3-py",
    "remote_url": "https://github.com/uber/h3-py",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "af962c0ab49562278f24970bc96290d25583d7c2",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "h3",
      "version": "4.5.0",
      "import_names": ["h3", "h3.api.basic_str", "h3.api.basic_int", "h3.api.memview_int", "h3.api.numpy_int"]
    }
  ],
  "submodules": [
    {
      "path": "src/h3lib",
      "commit": "1b536c34225191ba24a75a840f634d4a48c3b206"
    }
  ],
  "evidence": {
    "source_roots": ["src/h3", "src/h3/_h3shape.py"],
    "docs": ["readme.md", "docs/api_quick.md", "docs/api_comparison.md", "docs/polygon_tutorial.ipynb"],
    "examples": [],
    "tests": ["tests/test_lib", "tests/readme.md"],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, refresh.
- If the current dirty paths differ materially from `skills/`, refresh.
- If the H3 package version, public API modules, or H3 core submodule changes,
  refresh before relying on this skill for exact behavior.
- The `tests/test_cython` area is intentionally not part of this public
  operating-skill baseline because the repository describes that API as
  unsupported for external consumers.
