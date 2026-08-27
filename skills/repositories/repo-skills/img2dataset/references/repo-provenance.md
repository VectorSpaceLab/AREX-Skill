# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `img2dataset`. If the repository commit, working tree state, package version, or evidence paths differ from this snapshot, run a refresh workflow before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:32:28Z",
  "repository": {
    "name": "img2dataset",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "95523bc7579745a1749b8132d408b9fea89a338e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "img2dataset",
      "version": "1.47.0",
      "import_names": ["img2dataset"]
    }
  ],
  "evidence": {
    "source_roots": ["img2dataset"],
    "docs": ["README.md", "dataset_examples", "examples", "notebook", "img2dataset/architecture.md"],
    "tests": ["tests"],
    "configs": ["setup.py", "requirements.txt", "requirements-test.txt", "Makefile"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and refresh it.
- If the working tree dirty paths change materially, refresh it.
- If the public package version or entry point changes even on the same commit, refresh it.

## Evidence Notes

- Public runtime behavior was confirmed from the installed package version and a prepared inspection environment.
- The repository is treated as a dataset-processing package, not as a model-training repository.
- Keep private environment paths, command logs, and checkout-local details out of public runtime files.
