# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package/runtime evidence, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:29:17Z",
  "repository": {
    "name": "tensorflow-yolov3",
    "remote_url": "https://github.com/YunYang1994/tensorflow-yolov3.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "03cb272af2e26d598c553f3a2d38024fc6f67a0b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["core", "mAP"]
    },
    {
      "name": "tensorflow",
      "version": "1.15.5-inspection-compatible",
      "import_names": ["tensorflow"]
    }
  ],
  "evidence": {
    "source_roots": ["core", "mAP"],
    "docs": ["README.md", "docs/requirements.txt", "mAP/extra/README.md"],
    "examples": ["image_demo.py", "video_demo.py", "train.py", "evaluate.py", "convert_weight.py", "freeze_graph.py", "from_darknet_weights_to_ckpt.py", "from_darknet_weights_to_pb.py", "scripts/voc_annotation.py", "scripts/show_bboxes.py"],
    "tests": [],
    "configs": ["core/config.py", "data/classes", "data/anchors", "data/dataset"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source/config/doc changes beyond repo-local `skills/` artifacts, rerun or refresh the skill.
- If the repo adds package metadata, changes public scripts, changes `core/config.py`, or ports to TensorFlow 2.x, refresh the skill before relying on command/API details.
- If a future checkout contains real checkpoint/PB/data artifacts, this skill remains useful, but native verification can be extended with those artifacts.
