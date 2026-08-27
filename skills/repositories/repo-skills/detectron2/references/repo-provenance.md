# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Detectron2. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T19:17:41Z",
  "repository": {
    "name": "detectron2",
    "remote_url": "https://github.com/facebookresearch/detectron2",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "02b5c4e295e990042a714712c21dc79b731e8833",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "detectron2",
      "version": "0.6",
      "import_names": ["detectron2"]
    }
  ],
  "evidence": {
    "source_roots": ["detectron2"],
    "docs": ["README.md", "INSTALL.md", "GETTING_STARTED.md", "MODEL_ZOO.md", "docs/modules", "docs/tutorials", "docs/notes"],
    "examples": ["demo", "tools", "tools/deploy"],
    "tests": ["tests"],
    "configs": ["configs"],
    "projects": ["projects", "datasets/README.md"],
    "metadata": ["setup.py", "setup.cfg", "docs/requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, supported config paths, model-zoo APIs, public entry points, or project package mappings changed even on the same commit, run `refresh-repo-skill`.
- If Detectron2 major dependencies or build behavior changed, especially PyTorch, torchvision, OpenCV, Caffe2, ONNX, or CUDA extension support, run `refresh-repo-skill` before relying on installation/export guidance.
