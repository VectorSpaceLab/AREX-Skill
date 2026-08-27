# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, submodule state, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:50:41Z",
  "repository": {
    "name": "gaussian-splatting",
    "remote_url": "https://github.com/graphdeco-inria/gaussian-splatting.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "54c035f7834b564019656c3e3fcc3646292f727d",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/",
      "submodules/diff-gaussian-rasterization"
    ]
  },
  "packages": [
    {
      "name": "gaussian-splatting",
      "version": null,
      "import_names": [
        "arguments",
        "gaussian_renderer",
        "scene",
        "utils",
        "lpipsPyTorch"
      ]
    },
    {
      "name": "diff_gaussian_rasterization",
      "version": "0.0.0",
      "import_names": ["diff_gaussian_rasterization"]
    },
    {
      "name": "simple_knn",
      "version": "0.0.0",
      "import_names": ["simple_knn"]
    },
    {
      "name": "fused_ssim",
      "version": "0.0.0",
      "import_names": ["fused_ssim"]
    }
  ],
  "submodules": [
    {
      "path": "SIBR_viewers",
      "status": "not-initialized",
      "recorded_commit": "d8856f60c5384cc1975439193bb627d77d917d77"
    },
    {
      "path": "submodules/diff-gaussian-rasterization",
      "status": "initialized",
      "commit": "9c5c2028f6fbee2be239bc4c9421ff894fe4fbe0",
      "note": "nested third_party/glm was fetched for build inspection and differed from the recorded nested submodule commit"
    },
    {
      "path": "submodules/fused-ssim",
      "status": "initialized",
      "commit": "1272e21a282342e89537159e4bad508b19b34157"
    },
    {
      "path": "submodules/simple-knn",
      "status": "initialized",
      "commit": "86710c2d4b46680c02301765dd79e465819c8f19"
    }
  ],
  "evidence": {
    "source_roots": [
      "arguments/",
      "gaussian_renderer/",
      "scene/",
      "utils/",
      "lpipsPyTorch/"
    ],
    "docs": [
      "README.md",
      "results.md",
      "LICENSE.md"
    ],
    "scripts": [
      "train.py",
      "render.py",
      "metrics.py",
      "full_eval.py",
      "convert.py",
      "utils/make_depth_scale.py",
      "utils/read_write_model.py"
    ],
    "metadata": [
      "environment.yml",
      ".gitmodules"
    ],
    "tests": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If current submodule commits or initialized/uninitialized status differ materially from this snapshot, check affected setup and backend guidance.
- If package metadata, public CLI flags, or source file behavior changed even on the same commit, run `refresh-repo-skill`.
- If the current working tree is dirty in source areas other than generated `skills/`, compare those paths to the snapshot and refresh when behavior may differ.
