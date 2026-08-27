# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T00:00:00Z",
  "repository": {
    "name": "generative-models",
    "remote_url": "https://github.com/Stability-AI/generative-models.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e8cd657656fa5d61688191730d0e03242bf4ed44",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "sgm",
      "version": "0.1.0",
      "import_names": [
        "sgm"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "sgm",
      "main.py"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "scripts/sampling",
      "scripts/demo"
    ],
    "tests": [
      "tests/inference/test_inference.py"
    ],
    "configs": [
      "configs/inference",
      "configs/example_training",
      "scripts/sampling/configs"
    ],
    "requirements": [
      "requirements/pt2.txt"
    ]
  },
  "generated_skill": {
    "id": "stability-ai-generative-models",
    "sub_skills": [
      "inference-api",
      "video-sampling",
      "training-and-configs",
      "demos-and-watermarking"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, public APIs, script parameters, configs, or checkpoint naming changed, run `refresh-repo-skill`.
- Keep local environment paths, Python executable paths, cache paths, and credentials out of public skill content.
