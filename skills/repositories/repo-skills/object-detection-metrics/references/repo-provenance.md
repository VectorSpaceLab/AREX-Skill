# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package/version marker, CLI flags, core source modules, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:18:39Z",
  "repository": {
    "name": "Object-Detection-Metrics",
    "remote_url": "https://github.com/rafaelpadilla/Object-Detection-Metrics.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "803ec11ce5996629bbabd18e1bab6bf563d284fa",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The source checkout had an untracked skills/ production area. Source extraction excluded generated skill/test artifacts."
  },
  "packages": [
    {
      "name": "object-detection-metrics-source-toolkit",
      "version": "0.2 (beta)",
      "version_source": "pascalvoc.py VERSION constant",
      "import_names": [
        "BoundingBox",
        "BoundingBoxes",
        "Evaluator",
        "utils"
      ],
      "distribution_metadata": null,
      "packaging_note": "No pyproject.toml, setup.py, or setup.cfg was present; the repository is source-style rather than pip-installable."
    }
  ],
  "evidence": {
    "source_roots": [
      "lib/",
      "pascalvoc.py",
      "_init_paths.py"
    ],
    "docs": [
      "README.md",
      "samples/sample_1/README.md",
      "samples/sample_2/README.md"
    ],
    "examples": [
      "samples/sample_1/sample_1.py",
      "samples/sample_2/sample_2.py",
      "groundtruths/",
      "detections/",
      "groundtruths_rel/",
      "detections_rel/"
    ],
    "tests": [],
    "configs": [
      "requirements.txt"
    ],
    "reference_outputs": [
      "results/results.txt"
    ],
    "excluded": [
      ".github/",
      "aux_images/",
      "paper_survey_on_performance_metrics_for_object_detection_algorithms.pdf",
      "results/*.png",
      "skills/"
    ]
  }
}
```

## Refresh check

Run `refresh-repo-skill` when any of these are true:

- `git rev-parse HEAD` differs from the recorded commit.
- The working tree dirty state changes in source files, examples, requirements, or README guidance.
- `pascalvoc.py` flags, default AP method, coordinate validation, save-path behavior, or version marker changes.
- `lib/BoundingBox.py`, `lib/BoundingBoxes.py`, `lib/Evaluator.py`, or `lib/utils.py` change public signatures or metric behavior.
- The repository gains package metadata, console entry points, new supported metrics, or materially different examples.
- The user asks for COCO/UI/video metrics from the successor toolkit; that is not a refresh of this legacy skill but a separate source anchor.
