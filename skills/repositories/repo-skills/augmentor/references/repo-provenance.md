# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Augmentor. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:08:08Z",
  "repository": {
    "name": "Augmentor",
    "remote_url": "https://github.com/mdbloice/Augmentor.git",
    "vcs": "git",
    "branch": "master",
    "tag": "0.2.12",
    "commit": "894d5cc414205cf4becfb7c6f987b8c66feb9542",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "Augmentor",
      "version": "0.2.12",
      "import_names": ["Augmentor"]
    }
  ],
  "evidence": {
    "source_roots": ["Augmentor/"],
    "docs": ["README.md", "docs/userguide/", "docs/code.rst"],
    "examples": ["notebooks/"],
    "tests": ["tests/"],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt", "binder/environment.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths are not only generated skill/review artifacts, run `refresh-repo-skill` or inspect the changed source files first.
- If package metadata, public APIs, operation signatures, or optional dependency behavior changed even on the same commit, run `refresh-repo-skill`.
- If Augmentor is used with much newer Pillow, NumPy, pandas, Keras/TensorFlow, or torch/torchvision versions than the compatibility notes in this skill, run the bundled smoke helpers and refresh the troubleshooting guidance if behavior differs.
