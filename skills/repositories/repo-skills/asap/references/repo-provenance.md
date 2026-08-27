# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an ASAP checkout. If the repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:22:56Z",
  "repository": {
    "name": "ASAP",
    "remote_url": "https://github.com/LeCAR-Lab/ASAP",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "df5320cc47dd8cad97961bdfabfe402dd62ad999",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "asap",
      "version": "0.0.1",
      "import_names": ["humanoidverse"]
    },
    {
      "name": "sim2real",
      "version": "0.1.0",
      "import_names": ["sim2real"]
    },
    {
      "name": "isaac_utils",
      "version": "0.0.1",
      "import_names": ["isaac_utils"]
    }
  ],
  "evidence": {
    "source_roots": ["humanoidverse", "isaac_utils", "sim2real", "scripts"],
    "docs": ["README.md"],
    "examples": ["scripts/vis", "sim2real/rl_policy"],
    "tests": [],
    "configs": ["humanoidverse/config", "sim2real/config"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat the skill as potentially stale and refresh it.
- If the working tree becomes dirty and this snapshot is clean, refresh it.
- If package metadata, entry points, or backend prerequisites change, refresh it.

## Evidence Notes

The generated skill was distilled from these relative evidence paths:

- `README.md`
- `setup.py`
- `isaac_utils/setup.py`
- `sim2real/setup.py`
- `humanoidverse/`
- `isaac_utils/`
- `sim2real/`
- `scripts/`
