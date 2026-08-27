# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of deep-person-reid/Torchreid. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T20:07:08Z",
  "repository": {
    "name": "deep-person-reid",
    "remote_url": "https://github.com/KaiyangZhou/deep-person-reid.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f8cd150fdf77e8d9e1ed143b7f308c2c609ded50",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "torchreid",
      "version": "1.4.0",
      "import_names": ["torchreid"]
    }
  ],
  "evidence": {
    "source_roots": [
      "torchreid/"
    ],
    "docs": [
      "README.rst",
      "docs/user_guide.rst",
      "docs/datasets.rst",
      "docs/evaluation.rst",
      "docs/MODEL_ZOO.md",
      "docs/pkg/"
    ],
    "configs": [
      "configs/*.yaml"
    ],
    "scripts_and_tools": [
      "scripts/main.py",
      "scripts/default_config.py",
      "tools/compute_mean_std.py",
      "tools/parse_test_res.py",
      "tools/visualize_actmap.py",
      "tools/export.py"
    ],
    "native_candidates": [
      "torchreid/metrics/rank_cylib/test_cython.py",
      "script help checks for scripts/ and tools/",
      "synthetic FeatureExtractor/model/metrics cases"
    ],
    "excluded_long_tail": [
      "projects/DML/",
      "projects/OSNet_AIN/",
      "projects/attribute_recognition/",
      "torchreid/utils/GPU-Re-Ranking/extension/"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, run `refresh-repo-skill` or inspect the changed paths before use.
- If package metadata, public model/dataset registries, command-line flags, or export utilities changed even on the same commit, refresh this skill.
- If a task needs a workflow listed in `excluded_long_tail`, extend the skill with a new self-contained sub-skill rather than routing to source scripts from this snapshot.
