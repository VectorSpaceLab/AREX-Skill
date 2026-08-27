# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
Supervision. If the current commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill` before using
this skill as authoritative operating guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:18:27Z",
  "repository": {
    "name": "supervision",
    "remote_url": "https://github.com/roboflow/supervision.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "96e100ca1b7493984a9714d53117f8368300c749",
    "working_tree": "clean-before-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "supervision",
      "version": "0.31.0.dev0",
      "import_names": ["supervision"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/supervision"
    ],
    "docs": [
      "README.md",
      "docs",
      "examples/README.md",
      "AGENTS.md",
      ".github/CONTRIBUTING.md"
    ],
    "examples": [
      "examples/compact_mask",
      "examples/count_people_in_zone",
      "examples/heatmap_and_track",
      "examples/speed_estimation",
      "examples/time_in_zone",
      "examples/tracking",
      "examples/traffic_analysis"
    ],
    "tests": [
      "tests/detection",
      "tests/annotators",
      "tests/dataset",
      "tests/key_points",
      "tests/metrics",
      "tests/utils",
      "tests/draw",
      "tests/geometry",
      "tests/assets",
      "tests/cv2",
      "tests/test_public_api.py",
      "tests/test_validate_deprecations.py"
    ],
    "configs": [
      "pyproject.toml",
      "tox.ini",
      "mkdocs.yml"
    ]
  },
  "verification_baseline": {
    "inspection_environment_status": "ok",
    "required_backend": "cpu",
    "opencv_backend_observed": "fallback",
    "metrics_extra_observed": true,
    "geotiff_extra_observed": false
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale.
- If public package metadata, top-level exports, optional extras, deprecations,
  or source roots changed, refresh even on the same commit.
- If the current source checkout has user changes in source/docs/tests/examples
  that affect the workflows above, refresh or explicitly account for the local
  delta.
- Generated skill files, review artifacts, local environments, and caches are
  not part of the source evidence snapshot.
