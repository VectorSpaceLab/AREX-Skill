# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, public scripts, cfg files, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T03:35:00Z",
  "repository": {
    "name": "pytorch-yolo-v3",
    "remote_url": "https://github.com/ayooshkathuria/pytorch-yolo-v3.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "fbb4ef98d5a598f4c8eded6d618a599b7d289e2f",
    "working_tree": "clean-at-pre-generation-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["darknet", "util", "preprocess", "bbox"],
      "notes": "The repository has no pyproject.toml, setup.py, setup.cfg, requirements file, or console entry-point metadata; it is a script-oriented source repository."
    }
  ],
  "evidence": {
    "source_roots": ["darknet.py", "util.py", "preprocess.py", "bbox.py", "__init__.py"],
    "docs": ["README.md"],
    "scripts": ["detect.py", "video_demo.py", "video_demo_half.py", "cam_demo.py"],
    "configs": ["cfg/yolov3.cfg", "cfg/yolo.cfg", "cfg/yolo-voc.cfg", "cfg/tiny-yolo-voc.cfg"],
    "data": ["data/coco.names", "data/voc.names", "pallete"],
    "sample_assets": ["dog-cycle-car.png", "det_messi.jpg", "imgs/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the public scripts, cfg files, data names, or top-level modules listed above changed even on the same commit, run `refresh-repo-skill`.
- If the repository gains package metadata, tests, training code, or maintained installation requirements, refresh this skill because the current baseline treats the project as detection-only and script-oriented.
- If a downstream checkout has local patches for unsupported cfg block types, headless video export, custom class heads, or CUDA camera behavior, use this skill as a baseline but verify the patched behavior separately.
