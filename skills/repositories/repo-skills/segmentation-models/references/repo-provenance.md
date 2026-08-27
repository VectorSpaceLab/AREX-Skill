# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Segmentation Models. If the current repo commit, dirty state, package version, public constructors, dependency declarations, docs, examples, or tests differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:38:44Z",
  "repository": {
    "name": "segmentation_models",
    "remote_url": "https://github.com/qubvel/segmentation_models.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "5d24bbfb28af6134e25e2c0b79e7727f6c0491d0",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "segmentation-models",
      "version": "1.0.1",
      "import_names": ["segmentation_models"]
    }
  ],
  "evidence": {
    "source_roots": [
      "segmentation_models/",
      "segmentation_models/models/",
      "segmentation_models/backbones/",
      "segmentation_models/base/"
    ],
    "docs": [
      "README.rst",
      "docs/install.rst",
      "docs/tutorial.rst",
      "docs/api.rst",
      "docs/support.rst"
    ],
    "examples": [
      "examples/binary segmentation (camvid).ipynb",
      "examples/multiclass segmentation (camvid).ipynb"
    ],
    "tests": [
      "tests/test_models.py",
      "tests/test_metrics.py",
      "tests/test_utils.py"
    ],
    "package_metadata": [
      "setup.py",
      "requirements.txt",
      "MANIFEST.in",
      "segmentation_models/__version__.py"
    ],
    "repo_owned_scripts": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, constructor signatures, backbone names, loss/metric APIs, examples, tests, or install/backend requirements changed even on the same commit, run `refresh-repo-skill`.
- If future Segmentation Models releases target Keras 3, TensorFlow 2-only APIs, new model families, or different dependency names, refresh this skill before relying on version-specific guidance.
