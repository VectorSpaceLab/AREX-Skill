# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the repository commit, dirty state, package version, or major evidence paths differ from this snapshot, run a refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:24:44Z",
  "repository": {
    "name": "PerceptualSimilarity",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "082bb24f84c091ea94de2867d34c4544f68e0963",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "lpips",
      "version": "0.1.4",
      "import_names": ["lpips"]
    }
  ],
  "evidence": {
    "source_roots": ["lpips", "data", "util"],
    "docs": ["README.md"],
    "examples": ["imgs", "lpips_1dir_allpairs.py", "lpips_2dirs.py", "lpips_2imgs.py", "lpips_loss.py", "test_network.py"],
    "tests": ["test_dataset_model.py", "test_network.py"],
    "scripts": ["scripts"],
    "configs": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, refresh this skill.
- If the working tree dirty paths change materially, refresh this skill.
- If the public package version or entry-point behavior changes, refresh this skill.
