# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:43:37Z",
  "repository": {
    "name": "colorization",
    "remote_url": "https://github.com/richzhang/colorization.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4f6009ed1495b1300231ebeb41cc4015557ddef7",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["colorizers"],
      "packaging_note": "This checkout has no pyproject.toml, setup.py, or setup.cfg; import from a clone root or add the clone root to PYTHONPATH."
    }
  ],
  "evidence": {
    "source_roots": ["colorizers/"],
    "docs": ["README.md"],
    "examples": ["demo_release.py", "imgs/", "imgs_out/"],
    "tests": [],
    "configs": [],
    "requirements": ["requirements.txt"],
    "excluded": [".git/", "colorizers/__pycache__/", "skills/", "imgs/.DS_Store"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree's non-skill dirty paths differ from this snapshot, run `refresh-repo-skill`.
- If the repo gains package metadata, console entry points, new public model constructors, changed weight URLs, training workflows, or changed preprocessing/postprocessing signatures, run `refresh-repo-skill`.
- If downstream tasks require the unsupported Caffe branch or training behavior, build a separate skill from that branch/source instead of stretching this PyTorch test-time snapshot.
