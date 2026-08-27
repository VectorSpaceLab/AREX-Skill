# Repository Provenance

Read this before deciding whether the SimpleDet skill matches a checkout. If
the commit, dirty state, package/dependency contract, or major evidence paths
differ, refresh the skill rather than silently applying old guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T18:03:32Z",
  "repository": {
    "name": "simpledet",
    "remote_url": "https://github.com/tusen-ai/simpledet.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "97413463f0bc3116f684eaf7031fd3dd6ded3149",
    "working_tree": "clean before skill artifacts",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mxnet-cu101",
      "version": "1.6.0.post0 documented-compatible fallback; legacy custom beta wheel also documented",
      "import_names": ["mxnet"]
    },
    {
      "name": "mxnext",
      "version": "separate Git dependency; version is not pinned by repository metadata",
      "import_names": ["mxnext"]
    },
    {
      "name": "pycocotools",
      "version": "patched Git dependency documented by SimpleDet",
      "import_names": ["pycocotools"]
    }
  ],
  "evidence": {
    "source_roots": ["core", "symbol", "models", "operator_py", "utils"],
    "docs": ["README.md", "doc", "MODEL_ZOO.md", "models/*/README.md"],
    "examples": ["detection_train.py", "detection_test.py", "mask_test.py", "detection_infer_speed.py", "doc/fully_annotated_config.py"],
    "tests": ["unittest/test_loader.py"],
    "configs": ["config"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Check whether the root entry scripts, `core/`, `symbol/`, `models/`,
  `operator_py/`, `utils/`, or `config/` changed materially.
- Recheck the MXNet/mxnext/CUDA compatibility contract before changing any
  install or backend claim.
