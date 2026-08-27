# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:33:06Z",
  "repository": {
    "name": "DeepLabCut",
    "remote_url": "https://github.com/DeepLabCut/DeepLabCut.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v3.0.1",
    "commit": "2df0f46c8c8c56c8238b46b3d58384163bafb2f0",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Only repo-local skill production outputs were observed as untracked during generation. Treat source-code dirty state as unknown if other paths appear later."
  },
  "packages": [
    {
      "name": "deeplabcut",
      "version": "3.0.1",
      "import_names": ["deeplabcut"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "setup.py", "deeplabcut/version.py"],
    "source_roots": [
      "deeplabcut/",
      "deeplabcut/create_project/",
      "deeplabcut/generate_training_dataset/",
      "deeplabcut/pose_estimation_pytorch/",
      "deeplabcut/pose_estimation_tensorflow/",
      "deeplabcut/pose_tracking_pytorch/",
      "deeplabcut/modelzoo/",
      "deeplabcut/pose_estimation_3d/",
      "deeplabcut/post_processing/",
      "deeplabcut/refine_training_dataset/",
      "deeplabcut/utils/"
    ],
    "docs": [
      "README.md",
      "docs/installation.md",
      "docs/UseOverviewGuide.md",
      "docs/standardDeepLabCut_UserGuide.md",
      "docs/maDLC_UserGuide.md",
      "docs/pytorch/",
      "docs/ModelZoo.md",
      "docs/Overviewof3D.md",
      "docs/main-workflows/multi-animal-tracking.md",
      "docs/recipes/"
    ],
    "examples": ["examples/testscript_*.py", "examples/utils.py"],
    "tests": ["tests/", "testscript_cli.py"],
    "configs": [
      "deeplabcut/pose_cfg.yaml",
      "deeplabcut/inference_cfg.yaml",
      "deeplabcut/reid_cfg.yaml",
      "deeplabcut/modelzoo/project_configs/",
      "deeplabcut/modelzoo/model_configs/"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current tag, package version, public API exports, or package extras differ, run `refresh-repo-skill`.
- If the current working tree is dirty in source paths other than generated skill outputs, run `refresh-repo-skill` before relying on API details.
- If DeepLabCut changes its package entry point, TensorFlow support status, PyTorch config schema, Model Zoo inventories, or multi-animal tracking API, run `refresh-repo-skill`.
