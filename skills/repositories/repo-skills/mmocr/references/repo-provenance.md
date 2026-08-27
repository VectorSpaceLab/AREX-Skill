# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an MMOCR checkout. If the current repo commit, dirty source state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T20:04:22Z",
  "repository": {
    "name": "mmocr",
    "remote_url": "https://github.com/open-mmlab/mmocr.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "966296f26ac34cf0e96d40ab4a0a94c9a697909a",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mmocr",
      "version": "1.0.1",
      "import_names": ["mmocr"]
    },
    {
      "name": "mmcv",
      "version": "2.1.0",
      "import_names": ["mmcv"]
    },
    {
      "name": "mmengine",
      "version": "0.10.7",
      "import_names": ["mmengine"]
    },
    {
      "name": "mmdet",
      "version": "3.3.0",
      "import_names": ["mmdet"]
    }
  ],
  "evidence": {
    "source_roots": ["mmocr"],
    "package_metadata": ["setup.py", "setup.cfg", "requirements.txt", "requirements/"],
    "docs": ["README.md", "docs/en/get_started", "docs/en/user_guides", "docs/en/basic_concepts", "docs/en/api"],
    "configs": ["configs", "model-index.yml"],
    "datasets": ["dataset_zoo", "dicts"],
    "examples": ["demo"],
    "scripts": ["tools"],
    "tests": ["tests/test_apis", "tests/test_datasets", "tests/test_evaluation", "tests/test_structures", "tests/test_utils", "tests/test_visualization", "tests/test_models"],
    "projects": ["projects/README.md", "projects/example_project", "projects/ABCNet", "projects/SPTS"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public import paths, inferencer signatures, config families, dataset formats, or official command surfaces changed even on the same commit, refresh the skill.
- If current source files are dirty beyond generated skill/review artifacts, refresh before relying on the skill for updated behavior.
- If installed MMOCR, MMCV, MMEngine, or MMDetection versions differ materially, rerun the environment and script checks before executing workflows.
