# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a face.evoLVe checkout. If the current commit, dirty state, public entrypoints, or evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:56:16Z",
  "repository": {
    "name": "face.evoLVe",
    "remote_url": "https://github.com/ZhaoJ9014/face.evoLVe.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a9897bda52bdbb8d7c2fe28f1e21827dfd69d14e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "face.evoLVe source checkout",
      "version": null,
      "import_names": ["backbone", "head", "loss", "util", "applications.align", "paddle source modules"]
    },
    {
      "name": "torch",
      "version": "inspection verified with CPU PyTorch 2.4.1; README documents legacy PyTorch 1.0 era usage",
      "import_names": ["torch", "torchvision"]
    },
    {
      "name": "paddlepaddle",
      "version": "inspection verified with PaddlePaddle 2.6.2; Paddle README documents PaddlePaddle 2.1.0 era usage",
      "import_names": ["paddle"]
    }
  ],
  "evidence": {
    "source_roots": ["backbone/", "head/", "loss/", "util/", "applications/align/", "balance/", "data_processing/", "paddle/"],
    "docs": ["README.md", "paddle/README.md", "paddle/quant/README.md", "paddle/Paddle-Lite-Inference-demo/README.md"],
    "examples": ["applications/align/face_align.py", "applications/align/face_resize.py", "util/extract_feature_v1.py", "util/extract_feature_v2.py", "paddle/PaddleInference-demo/main.py", "paddle/Paddle-Lite-Inference-demo/main.py", "paddle/quant/quant_post_dynamic.py", "paddle/quant/quant_post_static.py"],
    "tests": [],
    "configs": ["config.py", "paddle/config.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If a checkout no longer has the source roots above, refresh before following API or script guidance.
- If `train.py`, `head/metrics.py`, or Paddle import behavior changed, refresh because several troubleshooting entries are tied to this snapshot.
- The repository has no `pyproject.toml`, `setup.py`, `setup.cfg`, or requirements file in this snapshot; if packaging metadata appears later, refresh the installation and import guidance.
