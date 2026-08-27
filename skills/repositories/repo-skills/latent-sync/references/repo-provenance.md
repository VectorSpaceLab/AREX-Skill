# Repository Provenance

Read this before deciding whether this skill is current for a LatentSync checkout. If the current repo commit, dirty state, package metadata, or major evidence paths differ materially from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:56:03Z",
  "repository": {
    "name": "LatentSync",
    "remote_url": "https://github.com/bytedance/LatentSync.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a229c3948406bc2cf6eaf4873e662e70c6a04746",
    "working_tree": "dirty",
    "dirty_paths": [
      "assets/demo1_video.mp4",
      "assets/demo2_video.mp4",
      "assets/demo3_video.mp4",
      "skills/disco/latent-sync",
      "skills/tests/latent-sync"
    ]
  },
  "packages": [
    {
      "name": "LatentSync source tree",
      "version": null,
      "import_names": ["latentsync", "scripts", "preprocess", "eval", "gradio_app"]
    }
  ],
  "evidence": {
    "source_roots": ["latentsync", "preprocess", "eval", "scripts", "tools"],
    "docs": ["README.md", "docs"],
    "examples": ["assets"],
    "tests": [],
    "configs": ["configs"]
  }
}
```

## Runtime baseline used during distillation

The source repo has no `pyproject.toml`, `setup.py`, or `setup.cfg`, so the repository was treated as a source tree rather than a packaged distribution.

The verified inspection baseline used Python `3.10.13`, `torch 2.5.1+cu121`, `torchvision 0.20.1+cu121`, `diffusers 0.32.2`, `transformers 4.48.0`, `decord 0.6.0`, `mediapipe 0.10.11`, `insightface 0.7.3`, `onnxruntime-gpu 1.21.0`, `gradio 5.24.0`, `numpy 1.26.4`, `setuptools 80.9.0`, and `ffmpeg 8.0.1`. CUDA allocation on 8× NVIDIA A100-SXM4-40GB was verified in the inspection environment.

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current dirty paths differ from the snapshot in a way that changes source code, configs, docs, assets, checkpoints, or scripts, refresh the skill.
- If new package metadata or public entry points are added to the repo, refresh the skill even if the commit is unchanged.
