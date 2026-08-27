# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Torch
Points3D. If the current repo commit, source dirty state, package version, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:18:36Z",
  "repository": {
    "name": "torch-points3d",
    "remote_url": "https://github.com/torch-points3d/torch-points3d.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "cf0061bd6db93b9d086b67a82babbdffa03646b4",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "torch-points3d",
      "version": "0.2.0",
      "import_names": ["torch_points3d"]
    }
  ],
  "evidence": {
    "source_roots": ["torch_points3d"],
    "docs": ["README.md", "docs/src/gettingstarted.rst", "docs/src/tutorials.rst", "docs/src/advanced.rst", "docs/src/api"],
    "examples": ["examples", "forward_scripts"],
    "tests": ["test"],
    "configs": ["conf"],
    "scripts": ["scripts/find_env.py", "scripts/find_runs.py", "scripts/omegaconf2dict.py", "scripts/sanity_check/scannet_check.py", "scripts/test_registration_scripts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If files under `torch_points3d/`, `conf/`, `docs/src/`, `examples/`, `forward_scripts/`, `train.py`, `eval.py`, or selected source `scripts/` changed, run `refresh-repo-skill`.
- Ignore generated `skills/` output when judging whether the source code changed; it is listed above only because the snapshot was produced inside the repository working tree.
- If package metadata, dependency pins, application API signatures, or Hydra command behavior changed even on the same commit, run `refresh-repo-skill`.
