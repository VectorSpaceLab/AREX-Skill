# Repository Provenance

## Purpose

Read this file when you need to decide whether the generated BEVFormer skill still matches the current checkout. If the commit, dirty state, or major evidence paths change, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:15:33Z",
  "repository": {
    "name": "BEVFormer",
    "remote_url": "https://github.com/fundamentalvision/BEVFormer.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "66b65f3a1f58caf0507cb2a971b9c0e7f842376c",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "torch",
      "version": "1.9.1+cu111",
      "import_names": ["torch"]
    },
    {
      "name": "mmcv-full",
      "version": "1.4.0",
      "import_names": ["mmcv"]
    },
    {
      "name": "mmdet",
      "version": "2.14.0",
      "import_names": ["mmdet"]
    },
    {
      "name": "mmsegmentation",
      "version": "0.14.1",
      "import_names": ["mmseg"]
    },
    {
      "name": "mmdet3d",
      "version": "0.17.1",
      "import_names": ["mmdet3d"]
    }
  ],
  "evidence": {
    "source_roots": ["projects/mmdet3d_plugin", "projects/configs", "tools"],
    "docs": ["README.md", "docs/install.md", "docs/getting_started.md", "docs/prepare_dataset.md"],
    "examples": [],
    "tests": [],
    "configs": ["projects/configs/_base_/default_runtime.py", "projects/configs/bevformer", "projects/configs/bevformer_fp16", "projects/configs/bevformerv2"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths change materially from this snapshot, refresh the skill.
- If the documented install stack or public entry points change, refresh the skill even when the commit is the same.

## Evidence Summary

The core workflow evidence came from `README.md`, `docs/install.md`, `docs/getting_started.md`, `docs/prepare_dataset.md`, `projects/configs/bevformer/`, `projects/configs/bevformer_fp16/`, `projects/configs/bevformerv2/`, `projects/mmdet3d_plugin/`, and `tools/`.
