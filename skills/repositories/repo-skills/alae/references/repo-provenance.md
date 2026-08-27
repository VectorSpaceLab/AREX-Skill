# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an ALAE checkout. If the current repository commit, dirty state, config/script layout, dependency surface, or generated evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on version-sensitive guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:16:45Z",
  "repository": {
    "name": "ALAE",
    "remote_url": "https://github.com/podgorskiy/ALAE.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "42bcf2e5f213ff1c919483678344f3da6bc90f8a",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The source checkout had an untracked skills/ production log before runtime skill artifacts were generated; source code files were otherwise read from the commit above."
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "defaults",
        "launcher",
        "model",
        "net",
        "checkpointer",
        "dataloader",
        "train_alae"
      ],
      "note": "This checkout has no setup.py, setup.cfg, or pyproject.toml; it is a script repository, not an installable distribution."
    }
  ],
  "evidence": {
    "source_roots": [
      "*.py at repository root",
      "dataset_preparation/",
      "make_figures/",
      "metrics/",
      "principal_directions/",
      "style_mixing/",
      "training_artifacts/download_all.py"
    ],
    "docs": [
      "README.md",
      "principal_directions/README.md"
    ],
    "configs": [
      "configs/bedroom.yaml",
      "configs/celeba.yaml",
      "configs/celeba-hq256.yaml",
      "configs/ffhq.yaml",
      "configs/mnist.yaml",
      "configs/mnist_fc.yaml",
      "defaults.py"
    ],
    "examples": [
      "interactive_demo.py",
      "style_mixing/stylemix.py",
      "make_figures/*.py",
      "dataset_samples/",
      "style_mixing/test_images/"
    ],
    "tests": [],
    "artifacts_excluded": [
      "style_mixing/output/",
      "make_figures/output/",
      "training_artifacts/*/*.pth",
      "principal_directions/direction_*.npy as binary runtime assets"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `42bcf2e5f213ff1c919483678344f3da6bc90f8a`, treat this skill as potentially stale.
- If the repository gains packaging metadata, console entry points, new configs, new metric scripts, or the missing ablation files (`model_separate.py`, `train_alae_separate.py`, `celeba_ablation_*.yaml`), refresh the skill.
- If PyTorch, TensorFlow, DareBlopy, dnnlib, or CUDA support changes materially, refresh environment and troubleshooting guidance.
- If `training_artifacts/download_all.py` changes model IDs/URLs or `last_checkpoint` conventions, refresh generation and setup guidance.
