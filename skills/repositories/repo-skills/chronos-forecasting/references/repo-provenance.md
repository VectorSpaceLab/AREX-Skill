# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Chronos Forecasting. If the current repo commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:25:53Z",
  "repository": {
    "name": "chronos-forecasting",
    "remote_url": "https://github.com/amazon-science/chronos-forecasting.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8589d1988e9676817548e9626738ff06b6ca6370",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "chronos-forecasting",
      "version": "2.3.1",
      "import_names": ["chronos"]
    }
  ],
  "evidence": {
    "source_roots": ["src/chronos"],
    "docs": ["README.md", "scripts/README.md"],
    "examples": ["notebooks/chronos-2-quickstart.ipynb", "notebooks/deploy-chronos-to-amazon-sagemaker.ipynb"],
    "tests": ["test/test_chronos.py", "test/test_chronos_bolt.py", "test/test_chronos2.py", "test/test_df_utils.py", "test/test_preprocess.py", "test/test_utils.py"],
    "configs": ["pyproject.toml", "scripts/training/configs", "scripts/evaluation/configs"],
    "scripts": ["scripts/kernel-synth.py", "scripts/training/train.py", "scripts/evaluation/evaluate.py", "scripts/evaluation/agg-relative-score.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, exported objects in `chronos.__all__`, public pipeline signatures, or model-loading behavior changed, refresh even on the same commit.
- Generated skill files under `skills/` were produced after the source snapshot and should not be treated as source-repo dirty state.
- If Chronos adds new public model families, CLI entry points, dependency extras, or changes the DataFrame/covariate schema, refresh the affected sub-skills.
