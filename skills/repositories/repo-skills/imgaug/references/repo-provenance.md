# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a checkout of imgaug. If the commit, dirty state, package version, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:13:25Z",
  "repository": {
    "name": "imgaug",
    "remote_url": "https://github.com/aleju/imgaug.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0101108d4fed06bc5056c4a03e2bcb0216dac326",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "imgaug",
      "version": "0.4.0",
      "import_names": ["imgaug"]
    }
  ],
  "evidence": {
    "source_roots": ["imgaug"],
    "docs": ["README.md", "CHANGELOG.md", "changelogs"],
    "examples": ["checks"],
    "tests": ["test"],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", ".github/workflows/test_master.yml"]
  }
}
```

## Refresh Check

- If the current commit differs from the recorded commit, treat this skill as potentially stale and refresh it.
- If the working tree changes from clean to dirty or the dirty path set changes, refresh it.
- If the package version, public import surface, or dependency/compatibility story changes, refresh it.
