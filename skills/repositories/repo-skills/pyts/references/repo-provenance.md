# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of pyts.
If the current commit, dirty state, package version, or major evidence paths
change, run a refresh pass instead of assuming the skill still matches.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T19:03:41Z",
  "repository": {
    "name": "pyts",
    "remote_url": "https://github.com/johannfaouzi/pyts.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4f3d97bcb1016d33dbfaef68c0931756a4552410",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pyts",
      "version": "0.13.0",
      "import_names": ["pyts"]
    }
  ],
  "evidence": {
    "source_roots": ["pyts"],
    "docs": ["README.md", "doc"],
    "examples": ["examples"],
    "tests": ["pyts/tests", "pyts/*/tests"],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "environment.yml", ".github/workflows"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as stale.
- If the repo becomes clean again or the dirty paths change materially, run a
  refresh pass before trusting the skill snapshot.
- If public package behavior changes even on the same commit, refresh the skill
  from the new evidence.
