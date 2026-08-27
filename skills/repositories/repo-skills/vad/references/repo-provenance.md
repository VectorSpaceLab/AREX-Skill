# Repository Provenance

## Purpose

Read this before deciding whether the skill matches a VAD checkout. If the commit, working-tree state, dependency family, or major evidence paths differ, run `refresh-repo-skill` before relying on detailed guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "VAD",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1688c4b1c3a9e2e7873ca9700ff8058170c0e3c8",
    "working_tree": "clean-at-inspection",
    "dirty_paths": []
  },
  "packages": [
    {"name": "torch", "version": "1.9.1+cu111", "import_names": ["torch"]},
    {"name": "mmcv-full", "version": "1.4.0", "import_names": ["mmcv"]},
    {"name": "mmdet", "version": "2.14.0", "import_names": ["mmdet"]},
    {"name": "mmsegmentation", "version": "0.14.1", "import_names": ["mmseg"]},
    {"name": "mmdetection3d", "version": "0.17.1", "import_names": ["mmdet3d"]},
    {"name": "nuscenes-devkit", "version": "1.1.9", "import_names": ["nuscenes"]}
  ],
  "evidence": {
    "source_roots": ["projects/mmdet3d_plugin", "VADv2"],
    "docs": ["README.md", "docs/install.md", "docs/prepare_dataset.md", "docs/train_eval.md", "docs/visualization.md"],
    "examples": [],
    "tests": [],
    "configs": ["projects/configs/VAD", "projects/configs/datasets/custom_nus-3d.py"],
    "scripts": ["tools/train.py", "tools/test.py", "tools/create_data.py", "tools/data_converter/vad_nuscenes_converter.py", "tools/analysis_tools/visualization.py"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare dirty paths and config/plugin/data script changes.
- Check whether the legacy package versions and public CLI flags still match.
- Refresh if VADv2 additions or custom dataset/result schemas change.

Paths in this file are relative evidence labels only; runtime workflows use the bundled skill references and helpers rather than reopening source files.
