# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run refresh generation.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T18:07:13Z",
  "repository": {
    "name": "BackgroundMattingV2",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a8e82df9f594578edf287dbb2b289ebcc50fbf00",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "BackgroundMattingV2",
      "version": null,
      "import_names": ["model", "dataset", "inference_utils"]
    }
  ],
  "evidence": {
    "source_roots": ["model", "dataset", "inference_utils.py", "data_path.py", "eval"],
    "docs": ["README.md", "doc/model_usage.md"],
    "examples": ["inference_images.py", "inference_video.py", "inference_webcam.py", "inference_speed_test.py", "export_onnx.py", "export_torchscript.py", "train_base.py", "train_refine.py"],
    "tests": [],
    "configs": ["requirements.txt", "data_path.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, refresh the skill.
- If the dirty paths change materially, refresh the skill.
- If the public CLI flags, model signatures, or backend support change, refresh
  the skill even on the same commit.
