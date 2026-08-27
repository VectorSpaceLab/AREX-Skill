# Repository Provenance

Read this before deciding whether the skill matches a checkout. If the commit,
package version, public entry points, or major evidence paths differ, use a
refresh workflow before relying on detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "braindecode",
    "remote_url": "https://github.com/braindecode/braindecode.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "eb3ddee6b72b07ff7457f9273cff179400b925c5",
    "working_tree": "clean-at-source-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "braindecode",
      "version": "1.8.0dev0",
      "import_names": ["braindecode"]
    }
  ],
  "evidence": {
    "source_roots": ["braindecode"],
    "docs": ["README.rst", "docs", "pyproject.toml"],
    "examples": ["examples"],
    "tests": ["test"],
    "configs": ["pyproject.toml", "setup.cfg"]
  }
}
```

## Refresh check

- Compare the current `git rev-parse HEAD` with the recorded commit.
- Compare package metadata and public exports, especially datasets,
  preprocessing, models, training wrappers, augmentation, and visualization.
- If the source checkout has changed or this snapshot was dirty, refresh before
  publishing a new version. This skill does not require the original checkout
  at runtime.
