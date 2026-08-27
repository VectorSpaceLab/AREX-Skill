# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package facts, or evidence
paths differ materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:20:32Z",
  "repository": {
    "name": "tencent-ml-images",
    "remote_url": "https://github.com/Tencent/tencent-ml-images.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "182631879cdb3d44d594d13d3f29a98bf7acdf81",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["flags", "models", "data_processing", "train", "finetune", "image_classification", "extract_feature"]
    }
  ],
  "evidence": {
    "source_roots": ["models", "data_processing", "data", "example"],
    "docs": ["README.md"],
    "examples": ["example"],
    "tests": [],
    "configs": ["flags.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and refresh it.
- If the dirty paths meaningfully differ from this snapshot, refresh it.
- If package metadata or public entry points change, refresh it.

## Notes

- The repository has no `pyproject.toml`, `setup.py`, or `setup.cfg` metadata,
  so the public runtime guidance is based on source and verified smoke facts
  rather than a packaged distribution.
- The verified smoke used a TensorFlow 1.6-compatible runtime and OpenCV for
  source inspection. See `references/setup-and-scope.md` for the public-facing
  summary.
