# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of KAG. If the current commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T11:25:08Z",
  "repository": {
    "name": "KAG",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "fdab15b3929d2ee40dfcdd388f90233096a6afc9",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "openspg-kag",
      "version": "0.8.0",
      "import_names": ["kag", "knext"]
    }
  ],
  "evidence": {
    "source_roots": ["kag", "knext"],
    "docs": ["README.md", "docs/quickstart.mdx", "docs/release_notes.md"],
    "examples": ["kag/examples", "kag/open_benchmark"],
    "tests": ["tests/unit"],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "pytest.ini", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale and refresh it.
- If the working tree dirty paths change materially, refresh it.
- If `openspg-kag` version or console entry points change, refresh it even on the same commit.
