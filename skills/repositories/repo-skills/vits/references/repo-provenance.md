# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:30:13Z",
  "repository": {
    "name": "vits",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2e561ba58618d021b5b8323d3765880f7e0ecfdb",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "vits",
      "version": null,
      "import_names": [
        "commons",
        "data_utils",
        "losses",
        "mel_processing",
        "models",
        "modules",
        "text",
        "monotonic_align",
        "utils"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "attentions.py",
      "commons.py",
      "data_utils.py",
      "losses.py",
      "mel_processing.py",
      "models.py",
      "modules.py",
      "text/",
      "monotonic_align/",
      "train.py",
      "train_ms.py",
      "preprocess.py",
      "utils.py"
    ],
    "docs": ["README.md"],
    "examples": ["inference.ipynb"],
    "tests": [],
    "configs": ["configs/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, refresh this skill.
- If the dirty paths differ materially, refresh this skill.
- If the dependency set or entry-point behavior changes, refresh this skill.
