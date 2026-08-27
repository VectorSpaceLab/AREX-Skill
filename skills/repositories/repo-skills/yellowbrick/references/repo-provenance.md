# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:34:25Z",
  "repository": {
    "name": "yellowbrick",
    "remote_url": "https://github.com/DistrictDataLabs/yellowbrick.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "f7a8e950bd31452ea2f5d402a1c5d519cd163fd5",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "yellowbrick",
      "version": "1.5",
      "import_names": [
        "yellowbrick"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "yellowbrick"
    ],
    "docs": [
      "README.md",
      "docs/api",
      "docs/changelog.rst"
    ],
    "examples": [
      "examples/README.md",
      "examples/cguan/dropping-curve.py",
      "selected notebooks as reference-only evidence"
    ],
    "tests": [
      "tests/test_classifier",
      "tests/test_regressor",
      "tests/test_features",
      "tests/test_cluster",
      "tests/test_model_selection",
      "tests/test_target",
      "tests/test_text",
      "tests/test_datasets",
      "tests/test_contrib",
      "tests/README.md"
    ],
    "configs": [
      "setup.py",
      "setup.cfg",
      "requirements.txt",
      "MANIFEST.in",
      ".github/workflows/ci.yml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot dirty paths differ, refresh before relying on exact API behavior.
- If package metadata, public imports, optional dependency behavior, or scikit-learn compatibility changes, refresh before using exact signatures.
- The dirty path recorded here is the generated `skills/` output/log area; source code evidence was taken from the tracked Yellowbrick package, docs, examples, tests, and metadata paths listed above.
