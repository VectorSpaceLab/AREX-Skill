# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Snips NLU. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:32:57Z",
  "repository": {
    "name": "snips-nlu",
    "remote_url": "https://github.com/snipsco/snips-nlu.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "74b2893c91fc0bafc919a7e088ecb0b2bd611acf",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Repo-local production log/artifact output was under skills/; source evidence for package behavior came from tracked package/docs/tests/sample files outside skills/."
  },
  "packages": [
    {
      "name": "snips-nlu",
      "version": "0.20.2",
      "model_version": "0.20.0",
      "import_names": ["snips_nlu"]
    }
  ],
  "entry_points": [
    "snips-nlu",
    "python -m snips_nlu"
  ],
  "evidence": {
    "source_roots": [
      "snips_nlu/",
      "snips_nlu_samples/"
    ],
    "docs": [
      "README.rst",
      "docs/source/quickstart.rst",
      "docs/source/tutorial.rst",
      "docs/source/dataset.rst",
      "docs/source/data_model.rst",
      "docs/source/cli.rst",
      "docs/source/evaluation.rst",
      "docs/source/languages.rst",
      "docs/source/builtin_entities.rst",
      "docs/source/api.rst"
    ],
    "examples": [
      "sample_datasets/",
      "snips_nlu_samples/sample.py",
      "snips_nlu_samples/sample_dataset.json"
    ],
    "tests": [
      "snips_nlu/tests/test_cli.py",
      "snips_nlu/tests/test_nlu_engine.py",
      "snips_nlu/tests/test_dataset_loading.py",
      "snips_nlu/tests/test_dataset_validation.py",
      "snips_nlu/tests/test_entity_loading.py",
      "snips_nlu/tests/test_result.py"
    ],
    "metadata": [
      "setup.py",
      "tox.ini",
      "MANIFEST.in",
      "snips_nlu/__about__.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata changes (`snips_nlu/__about__.py`, `setup.py`, console entry points, dependency ranges, or optional extras), refresh the skill even when public docs look unchanged.
- If language resource handling, dataset validation, CLI commands, or `SnipsNLUEngine` signatures change, refresh the owning sub-skill and re-run verification.
- If a checkout has only generated skill output under `skills/` as dirty state, that alone does not prove the source package behavior changed; inspect source/docs/test paths above before refreshing.
