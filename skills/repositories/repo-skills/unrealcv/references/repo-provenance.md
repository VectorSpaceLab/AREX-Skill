# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of UnrealCV. If the commit, branch, dirty state, or package version differs from this snapshot, run a refresh instead of assuming the generated skill is up to date.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T10:38:11Z",
  "repository": {
    "name": "unrealcv",
    "remote_url": "https://github.com/unrealcv/unrealcv.git",
    "vcs": "git",
    "branch": "5.2",
    "tag": null,
    "commit": "4bd1e3df9a37c0f9eb2f08c21c3739a8aeae1b34",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "UnrealCV",
      "version": "1.2.0",
      "import_names": ["unrealcv"]
    }
  ],
  "evidence": {
    "source_roots": ["client/python", "Source/UnrealCV"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["test/client"],
    "configs": ["client/python/pyproject.toml", "UnrealCV.uplugin"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as potentially stale and refresh it.
- If the current working tree is dirty when this snapshot says clean, or if the dirty paths differ, refresh it.
- If the public package version or import surface changes, refresh it even if the commit is unchanged.
