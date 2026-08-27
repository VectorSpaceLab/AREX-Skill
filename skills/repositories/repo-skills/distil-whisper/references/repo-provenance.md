# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of the repository. If the commit, dirty state, package versions, or evidence paths differ materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T20:00:00Z",
  "repository": {
    "name": "distil-whisper",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "cc96130f6e4cc74cab4545f3c6e7e5c204ced871",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "distil_whisper",
      "version": "0.0.1",
      "import_names": ["distil_whisper"]
    }
  ],
  "evidence": {
    "source_roots": ["training/flax/distil_whisper"],
    "docs": ["README.md", "training/README.md", "training/flax/README.md"],
    "examples": ["README.md examples", "training/flax/*_scripts"],
    "tests": [],
    "configs": ["training/pyproject.toml", "training/setup.py", "training/flax/pyproject.toml", "training/flax/setup.py", "training/flax/requirements.txt"]
  }
}
```

## Refresh check

- If the current commit differs from `repository.commit`, refresh the skill.
- If the working tree dirty paths differ materially from this snapshot, refresh the skill.
- If the bundled package versions or CLI signatures change, refresh the skill even when the commit is unchanged.
