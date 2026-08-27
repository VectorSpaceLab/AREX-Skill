# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of U-2-Net. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T16:32:56Z",
  "repository": {
    "name": "U-2-Net",
    "remote_url": "https://github.com/xuebinqin/U-2-Net.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ac7e1c817ecab7c7dff5ce6b1abba61cd213ff29",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "model",
        "data_loader"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "model/",
      "data_loader.py"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "u2net_test.py",
      "u2net_human_seg_test.py",
      "u2net_portrait_test.py",
      "u2net_portrait_demo.py",
      "u2net_portrait_composite.py",
      "gradio/demo.py"
    ],
    "tests": [
      "test_data/test_images",
      "test_data/test_human_images",
      "test_data/test_portrait_images"
    ],
    "configs": [
      "requirements.txt",
      "saved_models/face_detection_cv2/haarcascade_frontalface_default.xml"
    ],
    "training": [
      "u2net_train.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files, workflow scripts, dependency requirements, or checkpoint conventions changed, refresh the skill even on the same branch.
- This repository has no installable package version in the inspected snapshot; compare importable module behavior and evidence files directly.
