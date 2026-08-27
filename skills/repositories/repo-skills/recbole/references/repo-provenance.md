# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a RecBole checkout.
If the current repository commit, dirty source state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

The source checkout was clean before this skill and its review artifacts were
written. Generated `skills/` outputs are not part of the RecBole source evidence
baseline.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:33:09Z",
  "repository": {
    "name": "RecBole",
    "remote_url": "https://github.com/RUCAIBox/RecBole.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "7b02be5ec80a88310f2d04a27a82adfcbb5dc211",
    "working_tree": "clean-before-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "recbole",
      "version": "1.2.1",
      "import_names": ["recbole"]
    }
  ],
  "evidence": {
    "source_roots": [
      "recbole/"
    ],
    "docs": [
      "README.md",
      "README_CN.md",
      "docs/source/get_started/",
      "docs/source/user_guide/",
      "docs/source/developer_guide/"
    ],
    "examples": [
      "run_recbole.py",
      "run_recbole_group.py",
      "run_hyper.py",
      "significance_test.py",
      "run_example/",
      "hyper.test"
    ],
    "tests": [
      "tests/config/",
      "tests/data/",
      "tests/evaluation_setting/",
      "tests/metrics/",
      "tests/hyper_tuning/",
      "tests/model/",
      "tests/test_data/"
    ],
    "configs": [
      "recbole/properties/overall.yaml",
      "recbole/properties/model/",
      "recbole/properties/dataset/",
      "recbole/properties/quick_start_config/",
      "asset/model_list.json",
      "asset/dataset_list.json"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata changes (`setup.py`, `requirements.txt`, or
  `recbole/__init__.py`), refresh before relying on API signatures.
- If public docs, model/property YAMLs, quick-start APIs, data formats, or
  tests change materially, refresh the affected sub-skill.
- Ignore dirty paths that are only regenerated skill outputs or review artifacts
  when deciding whether the RecBole source evidence itself changed.
