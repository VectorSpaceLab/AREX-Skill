# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, public scripts, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:21:24Z",
  "repository": {
    "name": "photo2cartoon",
    "remote_url": "https://github.com/minivision-ai/photo2cartoon.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "6204e27a71620500c2f5b2ffd36646b0e2e5c110",
    "working_tree": "source-clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [],
  "source_distribution": {
    "installable_package": false,
    "package_version": null,
    "import_names": ["models", "utils", "dataset"]
  },
  "evidence": {
    "source_roots": ["models", "utils", "dataset.py", "train.py", "test.py", "test_onnx.py", "data_process.py", "predict.py"],
    "docs": ["README.md", "README_EN.md", "dataset/README.md"],
    "configs": ["cog.yaml", ".gitignore"],
    "examples": ["images/photo_test.jpg", "images/results.png", "images/data_process.jpg"],
    "tests": [],
    "existing_skills": ["skills/photo2cartoon.log"]
  },
  "external_assets_not_in_snapshot": [
    "models/photo2cartoon_weights.pt",
    "models/photo2cartoon_weights.onnx",
    "models/model_mobilefacenet.pth",
    "utils/seg_model_384.pb",
    "dataset/photo2cartoon/"
  ]
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If public scripts, model class signatures, preprocessing logic, Cog config, dataset layout docs, or README asset/dependency guidance changed, refresh even on the same commit.
- If a fork adds packaging metadata (`pyproject.toml`, `setup.py`, console entry points, requirements files), refresh before relying on install guidance.
- If external asset filenames or checkpoint keys differ from those above, refresh or extend the skill before publishing runtime instructions.
