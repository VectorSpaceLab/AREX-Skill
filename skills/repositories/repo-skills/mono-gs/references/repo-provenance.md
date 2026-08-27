# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package metadata, submodule
state, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:05:36Z",
  "repository": {
    "name": "MonoGS",
    "remote_url": "https://github.com/muskie82/MonoGS.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6c9254c319d8bff5caeef65259e6bb0941a9b9f6",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/",
      "submodules/diff-gaussian-rasterization/",
      "submodules/simple-knn/"
    ],
    "submodules": [
      {
        "path": "submodules/diff-gaussian-rasterization",
        "commit": "43e21bff91cd24986ee3dd52fe0bb06952e50ec7"
      },
      {
        "path": "submodules/diff-gaussian-rasterization/third_party/glm",
        "commit": "5c46b9c07008ae65cb81ab79cd677ecc1934b903"
      },
      {
        "path": "submodules/simple-knn",
        "commit": "44f764299fa305faf6ec5ebd99939e0508331503"
      }
    ]
  },
  "packages": [
    {
      "name": "MonoGS",
      "version": null,
      "import_names": [
        "slam",
        "utils",
        "gaussian_splatting",
        "gui",
        "simple_knn",
        "diff_gaussian_rasterization"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "slam.py",
      "utils/",
      "gaussian_splatting/",
      "gui/",
      "submodules/simple-knn/",
      "submodules/diff-gaussian-rasterization/"
    ],
    "docs": [
      "README.md",
      "Dependencies.md",
      "LICENSE.md"
    ],
    "examples": [
      "README.md command blocks"
    ],
    "tests": [],
    "configs": [
      "configs/live/",
      "configs/mono/",
      "configs/rgbd/",
      "configs/stereo/"
    ],
    "scripts": [
      "scripts/download_tum.sh",
      "scripts/download_replica.sh",
      "scripts/download_euroc.sh"
    ]
  },
  "environment_baseline": {
    "python": "3.7.x",
    "pytorch": "1.12.1",
    "cuda": "11.6",
    "required_backend": "cuda",
    "optional_hardware": ["Intel RealSense camera"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If submodule commits differ, refresh the install/backend and renderer guidance.
- If configs, dataset parsers, `slam.py`, frontend/backend classes, evaluation
  functions, or GUI/RealSense code changed, refresh the relevant sub-skills.
- If the current working tree is dirty in different source paths than this
  snapshot, inspect whether those changes alter public workflows before using
  this skill for exact commands.
