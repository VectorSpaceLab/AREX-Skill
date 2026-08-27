# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:09:07Z",
  "repository": {
    "name": "Informer2020",
    "remote_url": "https://github.com/zhouhaoyi/Informer2020.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "29f2a739226a509202a092b464163da81fa74960",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Generated skill/test artifacts are untracked; source modules were otherwise read from the recorded commit."
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["data", "exp", "models", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["data/", "exp/", "models/", "utils/", "main_informer.py"],
    "docs": ["README.md"],
    "examples": ["scripts/ETTh1.sh", "scripts/ETTh2.sh", "scripts/ETTm1.sh", "scripts/WTH.sh"],
    "tests": [],
    "configs": ["requirements.txt", "environment.yml", "Dockerfile", "Makefile"],
    "excluded": [".git/", "img/", "skills/tests/", "skills/Informer2020.log", "checkpoints/", "results/", "downloaded dataset CSVs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If source modules, the forecasting launcher, dataset loaders, benchmark command families, or dependency files changed, refresh the skill even on the same commit.
- If the current checkout has dirty source-code changes outside generated skill/test artifacts, refresh the skill before trusting workflow details.
