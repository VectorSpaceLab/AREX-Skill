# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of GluonCV. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:11:34Z",
  "repository": {
    "name": "gluon-cv",
    "remote_url": "https://github.com/dmlc/gluon-cv.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "567775619f3b97d47e7c360748912a4fd883ff52",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "gluoncv",
      "version": "0.11.0",
      "import_names": [
        "gluoncv"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "gluoncv/"
    ],
    "docs": [
      "README.md",
      "docs/install/",
      "docs/model_zoo/",
      "docs/tutorials/index.rst",
      "docs/tutorials_torch/index.rst",
      "docs/api/"
    ],
    "examples_and_scripts": [
      "scripts/"
    ],
    "tests": [
      "tests/unittests/",
      "tests/model_zoo/",
      "tests/model_zoo_torch/",
      "tests/auto/",
      "tests/onnx/"
    ],
    "configs": [
      "scripts/action-recognition/configuration/",
      "gluoncv/torch/engine/config/"
    ],
    "package_metadata": [
      "setup.py",
      "MANIFEST.in"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ materially from `dirty_paths`, run `refresh-repo-skill` or inspect the difference before trusting workflow details.
- If `gluoncv/__init__.py`, `setup.py`, public model registries, script families, dataset/transforms APIs, or docs/tutorial routes changed, refresh even on the same commit.
- If a future environment uses newer MXNet, PyTorch, NumPy, Pillow, AutoGluon, ONNX, or TVM stacks than those described in `references/install-and-backends.md`, rerun the root environment checker and update troubleshooting notes if behavior changed.
