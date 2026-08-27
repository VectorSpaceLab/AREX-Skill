# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Mask_RCNN checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:25:26Z",
  "repository": {
    "name": "Mask_RCNN",
    "remote_url": "https://github.com/matterport/Mask_RCNN.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "3deaec5d902d16e1daf56b62d5971d428dc920bc",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "mask-rcnn",
      "version": "2.1",
      "import_names": ["mrcnn"]
    }
  ],
  "evidence": {
    "source_roots": ["mrcnn"],
    "docs": ["README.md", "samples/balloon/README.md", "samples/nucleus/README.md"],
    "examples": [
      "samples/demo.ipynb",
      "samples/shapes/shapes.py",
      "samples/shapes/train_shapes.ipynb",
      "samples/balloon/balloon.py",
      "samples/coco/coco.py",
      "samples/nucleus/nucleus.py"
    ],
    "tests": [],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source changes outside generated skill/artifact directories, run `refresh-repo-skill`.
- If package metadata, TensorFlow/Keras compatibility, sample CLIs, or public `mrcnn` API signatures changed, run `refresh-repo-skill`.
- If a fork modernizes the package for TensorFlow 2/Keras 3, refresh the compatibility and troubleshooting references before using this skill for graph construction or training.
