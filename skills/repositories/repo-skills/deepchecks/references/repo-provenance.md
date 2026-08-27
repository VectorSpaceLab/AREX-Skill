# Repository Provenance

## Purpose

Read this before deciding whether this Deepchecks repo skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, optional extras, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T13:51:35Z",
  "repository": {
    "name": "deepchecks",
    "remote_url": "https://github.com/deepchecks/deepchecks.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "98475d17b08a21fca29d533b94b8ec3c70544a85",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "deepchecks",
      "version": "0.18.0.dev1",
      "import_names": ["deepchecks"]
    }
  ],
  "evidence": {
    "source_roots": [
      "deepchecks/",
      "deepchecks/core/",
      "deepchecks/tabular/",
      "deepchecks/nlp/",
      "deepchecks/vision/"
    ],
    "metadata": [
      "setup.py",
      "VERSION",
      "requirements/requirements.txt",
      "requirements/nlp-requirements.txt",
      "requirements/nlp-prop-requirements.txt",
      "requirements/vision-requirements.txt"
    ],
    "docs": [
      "README.md",
      "docs/source/getting-started/installation.rst",
      "docs/source/tabular/",
      "docs/source/nlp/",
      "docs/source/vision/",
      "docs/source/general/usage/",
      "docs/source/general/integrations/"
    ],
    "examples": [
      "examples/examples_supported_models.py",
      "examples/examples_metrics_guide.py",
      "examples/cicd/airflow.py",
      "examples/integrations/"
    ],
    "tests": [
      "tests/base/",
      "tests/serialization/",
      "tests/tabular/",
      "tests/nlp/",
      "tests/vision/"
    ],
    "excluded_or_reference_only": [
      "benchmarks/",
      ".github/",
      "extensive_testing/",
      "docs/source/_static/",
      "deepchecks.egg-info/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from this snapshot, review whether the changes touch Deepchecks source, docs, examples, tests, or requirements before trusting the skill.
- If `VERSION`, optional extras, public suite/check signatures, `Dataset`, `TextData`, `VisionData`, or result serialization APIs changed, run `refresh-repo-skill`.
- The snapshot was generated from a checkout where `skills/` was already untracked; this does not by itself describe Deepchecks package behavior.
