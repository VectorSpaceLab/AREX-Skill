# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout or release of SAHI. If the current repo commit, dirty state, package version, public entry points, optional dependency matrix, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on exact signatures or troubleshooting notes.

## Snapshot

The source snapshot was captured before writing this generated skill output.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:27:20Z",
  "repository": {
    "name": "sahi",
    "remote_url": "https://github.com/obss/sahi.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c9812dfa38e176a758b9acb5dabb7a99e0558055",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "sahi",
      "version": "0.12.5",
      "import_names": ["sahi"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "MANIFEST.in"],
    "source_roots": ["sahi"],
    "docs": [
      "README.md",
      "docs/quick-start.md",
      "docs/cli.md",
      "docs/predict.md",
      "docs/slicing.md",
      "docs/coco.md",
      "docs/fiftyone.md",
      "docs/guides/models.md",
      "docs/guides/sliced-inference.md",
      "docs/models",
      "docs/postprocess",
      "docs/utils",
      "docs/annotation.md",
      "docs/prediction.md",
      "docs/auto_model.md"
    ],
    "examples": ["demo"],
    "tests": [
      "tests/test_annotation.py",
      "tests/test_prediction.py",
      "tests/test_slicing.py",
      "tests/test_coco_utils.py",
      "tests/test_combine.py",
      "tests/test_predict.py",
      "tests/test_*model*.py",
      "tests/test_cv_utils.py",
      "tests/test_file_utils.py",
      "tests/test_import_utils.py",
      "tests/test_shapely_utils.py",
      "tests/test_table.py",
      "tests/data"
    ],
    "cli_and_scripts": ["sahi/cli.py", "sahi/scripts", "scripts/detect_batch.py"],
    "ci": [".github/workflows/ci.yml"]
  },
  "excluded_or_deprioritized": [
    "docs/tr",
    "docs/zh",
    "docs/images",
    "resources",
    "release/publish workflows",
    "root maintainer formatting scripts",
    "generated review artifacts"
  ],
  "verification_scope": {
    "required_backend": "cpu/base package",
    "optional_backends_not_required": [
      "cuda",
      "mps",
      "numba",
      "torchvision",
      "ultralytics",
      "transformers",
      "yolov5",
      "mmdet",
      "detectron2",
      "roboflow",
      "onnx",
      "pycocotools",
      "fiftyone"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, optional extras, console entry points, or supported `model_type` wrappers changed, refresh the skill even if the commit is nearby.
- If the current checkout changes public modules under `sahi/`, docs for CLI/model/postprocess/COCO workflows, or representative tests, refresh before relying on exact API guidance.
- If a later task requires a previously optional backend as a hard guarantee, prepare and verify that backend before claiming it is supported in the target runtime.
