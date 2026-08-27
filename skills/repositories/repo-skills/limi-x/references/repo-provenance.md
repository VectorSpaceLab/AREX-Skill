# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package model, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:38:42Z",
  "repository": {
    "name": "LimiX",
    "remote_url": "https://github.com/limix-ldm-ai/LimiX.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "61ede97e37d3eaae9e4500c0bba02965a2370eba",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["inference", "model", "utils", "retrieval_extension"],
      "packaging_note": "No pyproject.toml, setup.py, or setup.cfg existed in the inspected snapshot; source checkout import path is required."
    }
  ],
  "evidence": {
    "source_roots": ["inference", "model", "utils", "retrieval_extension/retrieval_search_space"],
    "docs": ["README.md", "README_cn.md", "doc/Usage_tips.md", "doc/Usage_tips_cn.md", "Dockerfile", "environment.yml"],
    "examples": ["examples/demo_classification.py", "examples/demo_regression.py", "examples/demo_missing_value_imputation.py"],
    "tests": [],
    "configs": ["config/*.json"],
    "scripts": ["inference_classifier.py", "inference_regression.py"],
    "benchmarks": ["benchmark_list/*.csv"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source/config/doc changes outside generated skill artifacts, run `refresh-repo-skill`.
- If package metadata is added, public import roots change, config filenames/keys change, or `LimiXPredictor` signatures change, run `refresh-repo-skill`.
- If future LimiX releases add packaging, official console entry points, additional model families, or changed checkpoint formats, refresh before relying on this skill for installation or CLI guidance.
