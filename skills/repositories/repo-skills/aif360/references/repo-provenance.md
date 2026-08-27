# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
AIF360 repository. If the current repo commit, dirty state, package version, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T08:37:19Z",
  "repository": {
    "name": "AIF360",
    "remote_url": "https://github.com/Trusted-AI/AIF360.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "34877916b789e569edf5c0aac033403ca90f34b3",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "aif360",
      "version": "0.6.1",
      "import_names": ["aif360"]
    }
  ],
  "evidence": {
    "source_roots": [
      "aif360/datasets",
      "aif360/metrics",
      "aif360/algorithms",
      "aif360/sklearn",
      "aif360/detectors",
      "aif360/explainers"
    ],
    "docs": [
      "README.md",
      "docs/source/Getting Started.rst",
      "docs/source/modules"
    ],
    "examples": [
      "examples",
      "examples/sklearn"
    ],
    "tests": [
      "tests",
      "tests/sklearn"
    ],
    "configs": [
      "setup.py",
      "requirements.txt",
      "MANIFEST.in"
    ],
    "reference_only": [
      "aif360/aif360-r",
      "mlops"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the package version or optional extras in package metadata differ, refresh
  the skill before relying on install or API claims.
- If major files under `aif360/datasets`, `aif360/metrics`, `aif360/algorithms`,
  `aif360/sklearn`, `aif360/detectors`, or `aif360/explainers` changed, refresh
  even if the version number did not change.
- The snapshot was dirty because generated production artifacts were under
  `skills/`; changes outside generated skill/artifact paths need independent
  review before reusing this skill as current.
