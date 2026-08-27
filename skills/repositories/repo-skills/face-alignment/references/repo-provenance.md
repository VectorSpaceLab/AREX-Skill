# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T18:12:26Z",
  "repository": {
    "name": "face-alignment",
    "remote_url": "https://github.com/1adrianb/face-alignment",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "608505febb47082eb83c2e54254294b3044d976f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "face-alignment",
      "version": "1.5.0",
      "import_names": ["face_alignment"]
    }
  ],
  "evidence": {
    "source_roots": ["face_alignment"],
    "docs": ["README.md"],
    "examples": ["examples"],
    "tests": ["test"],
    "configs": ["requirements.txt", "setup.py", "setup.cfg", "tox.ini", ".github/workflows/test.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
