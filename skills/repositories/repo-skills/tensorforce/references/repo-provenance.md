# Repository Provenance

## Purpose

Read this before deciding whether this Tensorforce skill is current for a checkout or installed package. If the current commit, dirty state, package version, or public evidence paths differ materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T18:09:45Z",
  "repository": {
    "name": "tensorforce",
    "remote_url": "https://github.com/tensorforce/tensorforce.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b05defa283d8054d3165740c74c6604aa38c81d4",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"],
    "dirty_note": "Dirty path is generated skill/review output from this construction run unless the current checkout shows additional source edits."
  },
  "packages": [
    {
      "name": "Tensorforce",
      "version": "0.6.5",
      "import_names": ["tensorforce"]
    }
  ],
  "evidence": {
    "source_roots": ["tensorforce/"],
    "docs": ["README.md", "docs/"],
    "examples": ["examples/"],
    "tests": ["test/"],
    "configs": ["benchmarks/configs/"],
    "scripts": ["run.py", "tune.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If public package metadata, import roots, agent/environment registries, examples, docs, or tests changed, refresh even if the commit is otherwise close.
- If a generated or local checkout has dirty paths outside generated skill/review artifacts, inspect those changes before using this skill as authoritative.
