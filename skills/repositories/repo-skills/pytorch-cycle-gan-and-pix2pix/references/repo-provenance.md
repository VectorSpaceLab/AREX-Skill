# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, dependency baseline, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:17:27Z",
  "repository": {
    "name": "pytorch-CycleGAN-and-pix2pix",
    "remote_url": "https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "2a7afba2895d52556dd5dfe07e8555ef657ced6f",
    "working_tree": "dirty-production-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["data", "models", "options", "util"]
    }
  ],
  "dependency_baseline": {
    "python": "3.11",
    "torch": "2.4.0",
    "torchvision": "0.19.0",
    "numpy": "1.24.3",
    "notes": "Repository has no pip distribution metadata; environment.yml is the primary dependency source."
  },
  "evidence": {
    "source_roots": ["data", "models", "options", "util", "train.py", "test.py"],
    "docs": ["README.md", "docs/overview.md", "docs/tips.md", "docs/qa.md", "docs/datasets.md", "docs/docker.md"],
    "scripts": ["datasets", "scripts"],
    "tests": ["scripts/test_before_push.py"],
    "configs": ["environment.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files under `data/`, `models/`, `options/`, `util/`, `train.py`, `test.py`, `datasets/`, `scripts/`, or `environment.yml` changed, refresh the skill.
- If the current checkout introduces packaging metadata, changes the supported Python/PyTorch baseline, or changes train/test entry-point behavior, refresh the skill.
- Ignore the presence of generated `skills/` production artifacts when comparing the public source baseline; they made the production checkout dirty but are not upstream runtime evidence.
