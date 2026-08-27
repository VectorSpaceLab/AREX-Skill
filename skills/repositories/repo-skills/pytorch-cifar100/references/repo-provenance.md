# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of pytorch-cifar100. If the current repo commit, dirty state, package/import layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:39:09Z",
  "repository": {
    "name": "pytorch-cifar100",
    "remote_url": "https://github.com/weiaicunzai/pytorch-cifar100.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "11d8418f415b261e4ae3cb1ffe20d06ec95b98e4",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["utils", "conf", "models"]
    }
  ],
  "evidence": {
    "source_roots": ["models", "conf", "utils.py", "dataset.py"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["conf/global_settings.py"],
    "scripts": ["train.py", "test.py", "lr_finder.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files under `models/`, `conf/`, `utils.py`, `dataset.py`, `train.py`, `test.py`, `lr_finder.py`, or `README.md` changed, refresh the skill even if the generated `skills/` tree is the only dirty path.
- If public CLI flags, model tokens, checkpoint names, data paths, or dependency/backend assumptions change, refresh the skill.
