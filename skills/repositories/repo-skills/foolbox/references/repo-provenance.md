# Repository Provenance

## Purpose

Read this before relying on version-sensitive details. If the current checkout
has a different commit, package version, public entry point, or evidence layout,
run a refresh of the repo skill before using it for exact API claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T00:00:00Z",
  "repository": {
    "name": "foolbox",
    "remote_url": "https://github.com/bethgelab/foolbox.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "2513a9a8675d7017e5266d3b0ed89124cb436ec5",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "foolbox",
      "version": "3.3.4",
      "import_names": ["foolbox"]
    }
  ],
  "evidence": {
    "source_roots": ["foolbox"],
    "docs": ["README.rst", "docs", "guide"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["setup.py", "setup.cfg", "pyproject.toml", "requirements.txt", "tests/requirements.txt"]
  }
}
```

## Refresh Check

- Compare the current Git commit with `2513a9a8675d7017e5266d3b0ed89124cb436ec5`.
- Recheck package metadata and public exports if `setup.py`, `foolbox/__init__.py`,
  wrapper modules, attack exports, or zoo modules changed.
- The source snapshot was clean at the recorded commit; the current dirty state
  includes generated skill material under `skills/`, not a source-code change.
