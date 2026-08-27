# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of mlxtend. If the current repo commit, dirty state, package version, dependency metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:08:48Z",
  "repository": {
    "name": "mlxtend",
    "remote_url": "https://github.com/rasbt/mlxtend.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9aadcee334f8b07003246d436cd9135b6d62a6b2",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The only observed dirty path was the skills output/log area used for this generation run; package source evidence was taken from tracked repository paths."
  },
  "packages": [
    {
      "name": "mlxtend",
      "version": "0.25.0",
      "import_names": ["mlxtend"]
    }
  ],
  "evidence": {
    "source_roots": [
      "mlxtend/",
      "mlxtend/classifier/",
      "mlxtend/regressor/",
      "mlxtend/cluster/",
      "mlxtend/evaluate/",
      "mlxtend/feature_selection/",
      "mlxtend/feature_extraction/",
      "mlxtend/preprocessing/",
      "mlxtend/frequent_patterns/",
      "mlxtend/plotting/",
      "mlxtend/data/",
      "mlxtend/file_io/",
      "mlxtend/text/",
      "mlxtend/math/",
      "mlxtend/utils/"
    ],
    "docs": [
      "README.md",
      "docs/sources/installation.md",
      "docs/sources/USER-GUIDE-INDEX.md",
      "docs/sources/user_guide/"
    ],
    "tests": [
      "mlxtend/classifier/tests/",
      "mlxtend/regressor/tests/",
      "mlxtend/cluster/tests/",
      "mlxtend/evaluate/tests/",
      "mlxtend/feature_selection/tests/",
      "mlxtend/feature_extraction/tests/",
      "mlxtend/preprocessing/tests/",
      "mlxtend/frequent_patterns/tests/",
      "mlxtend/plotting/tests/",
      "mlxtend/data/tests/",
      "mlxtend/text/tests/",
      "mlxtend/math/tests/",
      "mlxtend/utils/tests/"
    ],
    "configs": [
      "pyproject.toml",
      "requirements.txt",
      "uv.lock"
    ],
    "excluded": [
      ".git/",
      ".github/",
      "docs build helper scripts",
      "skills/tests/",
      "temp/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has package-source changes not represented by the snapshot, run `refresh-repo-skill`.
- If `mlxtend.__version__`, `pyproject.toml`, public imports, or documented dependency floors changed, refresh before relying on signatures or troubleshooting notes.
- If file IO, plotting, or frequent-pattern behavior has changed in newer tests, refresh because those areas include version-specific edge guidance.
