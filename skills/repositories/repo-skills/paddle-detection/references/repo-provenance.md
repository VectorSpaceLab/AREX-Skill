# Repository Provenance

Read this before deciding whether this skill matches a current PaddleDetection checkout. If the commit, tag, package metadata, or major evidence paths differ, run a refresh/re-extraction pass.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T18:54:28Z",
  "repository": {
    "name": "PaddleDetection",
    "remote_url": "https://github.com/PaddlePaddle/PaddleDetection.git",
    "vcs": "git",
    "branch": "release/2.9",
    "tag": "v2.9.0",
    "commit": "b25522a0f4bde8c80603f3ba5e3472059972e3b5",
    "working_tree": "clean before skill outputs",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "paddledet",
      "version": "0.0.0",
      "import_names": ["ppdet"]
    },
    {
      "name": "paddlepaddle",
      "version": "2.6.2 verified for inspection",
      "import_names": ["paddle"]
    }
  ],
  "evidence": {
    "source_roots": ["ppdet"],
    "docs": ["README_en.md", "docs/tutorials", "docs/tutorials/data", "docs/MODEL_ZOO_en.md", "deploy"],
    "examples": ["demo", "docs/tutorials/QUICK_STARTED.md", "deploy/pipeline/docs/tutorials"],
    "tests": ["ppdet/modeling/tests", "ppdet/model_zoo/tests", "test_tipc"],
    "configs": ["configs", "deploy/pipeline/config"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare the branch/tag and package version, especially the `setup.py` version and generated `ppdet/version.py`.
- Recheck `ppdet/core/workspace.py`, `ppdet/engine`, `ppdet/model_zoo`, `tools`, `deploy/python`, and `deploy/pipeline` if public flags or APIs changed.
- Treat a changed `requirements.txt`, PaddlePaddle compatibility range, model export format, or pipeline config schema as a refresh trigger.
