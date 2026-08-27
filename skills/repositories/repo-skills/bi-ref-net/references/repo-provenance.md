# Repository Provenance

## Purpose

Read this before deciding whether this BiRefNet skill is current for a checkout. If the current commit, dirty source files, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:05:00Z",
  "repository": {
    "name": "BiRefNet",
    "remote_url": "https://github.com/ZhengPeng7/BiRefNet.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "25cb9309bacf3dde954e4584594e16e142c51de5",
    "working_tree": "clean-at-source-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "config",
        "dataset",
        "image_proc",
        "inference",
        "loss",
        "utils",
        "models.birefnet",
        "models.backbones",
        "models.modules",
        "evaluation.metrics"
      ],
      "notes": "The repository has no pyproject.toml, setup.py, or setup.cfg; it is source-code-first and also exposes Hugging Face remote-code model workflows."
    }
  ],
  "evidence": {
    "source_roots": [
      "config.py",
      "dataset.py",
      "image_proc.py",
      "inference.py",
      "loss.py",
      "utils.py",
      "models/",
      "evaluation/"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "tutorials/BiRefNet_inference.ipynb",
      "tutorials/BiRefNet_inference_video.ipynb",
      "tutorials/BiRefNet_pth2onnx.ipynb"
    ],
    "scripts": [
      "train.py",
      "train.sh",
      "test.sh",
      "train_test.sh",
      "eval_existingOnes.py",
      "gen_best_ep.py",
      "sub.sh"
    ],
    "configs": [
      "config.py",
      "requirements.txt"
    ],
    "excluded_or_reference_only": [
      "rm_cache.sh",
      "make_a_copy.sh",
      ".git/",
      "repo-local generated/review artifacts"
    ]
  }
}
```

## Refresh Check

Refresh this skill when any of these are true:

- The current `HEAD` commit differs from `25cb9309bacf3dde954e4584594e16e142c51de5`.
- Source files such as `config.py`, `models/birefnet.py`, `dataset.py`, `inference.py`, `train.py`, `evaluation/metrics.py`, or `requirements.txt` have uncommitted changes not represented here.
- The repository gains packaging metadata, console entry points, new tutorials, new model-loading paths, or changed dependency/backend requirements.
- The user needs previously unverified optional workflows such as full CUDA inference, full training, ONNX conversion, or TensorRT deployment verified against current hardware and assets.
