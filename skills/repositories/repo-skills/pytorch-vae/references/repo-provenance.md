# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyTorch-VAE. If the checkout has moved to a different commit, branch, or dirty state, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T18:04:21Z",
  "repository": {
    "name": "PyTorch-VAE",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a6896b944c918dd7030e7d795a8c13e5c6345ec7",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "PyTorch-VAE source checkout",
      "version": null,
      "import_names": ["models", "experiment", "dataset", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["models/", "experiment.py", "dataset.py", "utils.py", "run.py"],
    "docs": ["README.md"],
    "tests": ["tests/"],
    "configs": ["configs/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, refresh this skill.
- If the dirty paths differ in a way that changes the source evidence, refresh this skill.
- If the model registry, config schema, or training runner changes, refresh this skill even when the commit stays the same.
