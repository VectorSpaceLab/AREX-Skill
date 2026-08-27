# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of TensorFlow Quantum. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run a refresh flow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:49:20Z",
  "repository": {
    "name": "quantum",
    "remote_url": "https://github.com/tensorflow/quantum.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9e378d1e3f21e4387120ecdf8506dfa058d338c8",
    "working_tree": "dirty: generated skill/review artifacts only",
    "dirty_paths": [
      "skills/disco/tensorflow-quantum/"
    ]
  },
  "packages": [
    {
      "name": "tensorflow-quantum",
      "version": "0.7.7",
      "import_names": ["tensorflow_quantum"]
    }
  ],
  "evidence": {
    "source_roots": ["tensorflow_quantum"],
    "docs": ["README.md", "docs"],
    "examples": ["docs/tutorials"],
    "tests": ["tensorflow_quantum/**/_test.py"],
    "configs": ["release/setup.py", "requirements.in", "requirements.txt", "requirements_lock_3_10.txt", "requirements_lock_3_11.txt", "requirements_lock_3_12.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the current working tree dirty paths differ materially from this snapshot, refresh it.
- If package metadata or public entry points change even on the same commit, refresh it.
