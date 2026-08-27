# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T22:39:45Z",
  "repository": {
    "name": "lanenet-lane-detection",
    "remote_url": "https://github.com/MaybeShewill-CV/lanenet-lane-detection.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "fb31c8e4877d08c548af6f93687727a687f8cd9b",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "lanenet-lane-detection",
      "version": null,
      "import_names": [
        "lanenet_model",
        "data_provider",
        "trainner",
        "semantic_segmentation_zoo",
        "local_utils"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "lanenet_model/",
      "data_provider/",
      "trainner/",
      "semantic_segmentation_zoo/",
      "local_utils/"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "data/training_data_example/",
      "data/tusimple_test_image/"
    ],
    "tests": [],
    "configs": [
      "config/tusimple_lanenet.yaml",
      "data/tusimple_ipm_remap.yml",
      "mnn_project/config.ini"
    ],
    "scripts": [
      "tools/generate_tusimple_dataset.py",
      "tools/make_tusimple_tfrecords.py",
      "tools/train_lanenet_tusimple.py",
      "tools/test_lanenet.py",
      "tools/evaluate_lanenet_on_tusimple.py",
      "mnn_project/freeze_lanenet_model.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, config keys, scripts, checkpoints, or public entry points changed even on the same commit, run `refresh-repo-skill`.
