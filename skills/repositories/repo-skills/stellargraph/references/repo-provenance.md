# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public API,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:44:25Z",
  "repository": {
    "name": "stellargraph",
    "remote_url": "https://github.com/stellargraph/stellargraph.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "3c2c8c18ab4c5c16660f350d8e23d7dc39e738de",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Generated skill, review artifacts, and production log were present under skills/ during this production run."
  },
  "packages": [
    {
      "name": "stellargraph",
      "version": "1.3.0b",
      "metadata_version": "1.3.0b0",
      "import_names": [
        "stellargraph"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "stellargraph/"
    ],
    "docs": [
      "README.md",
      "docs/index.rst",
      "docs/api.rst",
      "docs/hinsage.rst",
      "docs/glossary.rst"
    ],
    "examples": [
      "demos/README.md",
      "demos/basics/",
      "demos/node-classification/",
      "demos/link-prediction/",
      "demos/embeddings/",
      "demos/graph-classification/",
      "demos/time-series/",
      "demos/calibration/",
      "demos/ensembles/",
      "demos/interpretability/",
      "demos/connector/neo4j/"
    ],
    "tests": [
      "tests/core/",
      "tests/data/",
      "tests/mapper/",
      "tests/layer/",
      "tests/interpretability/",
      "tests/test_calibration.py",
      "tests/test_ensemble.py",
      "tests/test_losses.py",
      "tests/test_random.py",
      "tests/utils/"
    ],
    "configs": [
      "setup.py",
      "requirements.txt",
      "meta.yaml",
      "pytest.ini",
      ".github/workflows/ci.yml",
      ".buildkite/"
    ],
    "scripts_inventory": [
      "scripts/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, examples, tests, or package
  metadata changes not represented in the snapshot, refresh this skill.
- If a newer package version changes constructor signatures, generator/model
  pairing, TensorFlow/Keras compatibility, optional extras, dataset loaders, or
  Neo4j connector behavior, refresh this skill even if the repository path is
  similar.
- Ignore differences that are only regenerated review artifacts under `skills/`
  unless they correspond to changed runtime skill content.

## Important Version Notes

- The source version file reports `1.3.0b`; installed distribution metadata may
  normalize this pre-release as `1.3.0b0`.
- Package metadata declares Python `>=3.6,<3.9`. Do not assume modern Python or
  modern TensorFlow behavior without re-verification.
