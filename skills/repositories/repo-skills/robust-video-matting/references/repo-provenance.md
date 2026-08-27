# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
RobustVideoMatting. If the current repo commit, dirty state, source layout, or
public workflow files differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:37:12Z",
  "repository": {
    "name": "RobustVideoMatting",
    "remote_url": "https://github.com/PeterL1n/RobustVideoMatting.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "53d74c6826735f01f4406b5ca9075eee27bec094",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "model",
        "inference",
        "inference_utils",
        "dataset",
        "evaluation"
      ],
      "packaging_note": "This repository snapshot has no setup.py or pyproject.toml package metadata; workflows are source-checkout or TorchHub oriented."
    }
  ],
  "evidence": {
    "source_roots": [
      "model/",
      "dataset/",
      "evaluation/"
    ],
    "docs": [
      "README.md",
      "documentation/inference.md",
      "documentation/training.md"
    ],
    "scripts": [
      "inference.py",
      "inference_utils.py",
      "inference_speed_test.py",
      "train.py",
      "train_config.py",
      "train_loss.py",
      "hubconf.py",
      "documentation/misc/spd_preprocess.py"
    ],
    "requirements": [
      "requirements_inference.txt",
      "requirements_training.txt"
    ],
    "evaluation_scripts": [
      "evaluation/evaluate_lr.py",
      "evaluation/evaluate_hr.py",
      "evaluation/generate_imagematte_with_background_image.py",
      "evaluation/generate_imagematte_with_background_video.py",
      "evaluation/generate_videomatte_with_background_image.py",
      "evaluation/generate_videomatte_with_background_video.py"
    ],
    "excluded_as_runtime_evidence": [
      ".git/",
      "documentation/image/",
      "README_zh_Hans.md",
      "documentation/inference_zh_Hans.md",
      "generated review/test artifacts under skills/",
      "generated skill output under skills/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If source files under `model/`, `inference.py`, `inference_utils.py`,
  `hubconf.py`, `dataset/`, `train.py`, `train_config.py`, `train_loss.py`, or
  `evaluation/` changed, refresh before relying on API signatures or scripts.
- If package metadata is added later, refresh so install guidance can stop
  treating the repo as source-checkout oriented.
- If only generated files under `skills/` differ, that does not by itself make
  the source evidence stale.
