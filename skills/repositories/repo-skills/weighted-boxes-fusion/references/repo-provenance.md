# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a checkout of the repository. If the repository commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill instead of assuming it is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T19:27:23Z",
  "repository": {
    "name": "Weighted-Boxes-Fusion",
    "remote_url": "https://github.com/ZFTurbo/Weighted-Boxes-Fusion.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "96880f3df8d45ac21dce8d243fcfab420cadda47",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "ensemble_boxes",
      "version": "1.0.9",
      "import_names": ["ensemble_boxes"]
    }
  ],
  "evidence": {
    "source_roots": ["ensemble_boxes"],
    "docs": ["README.md", "CHANGES.md", "docs/notable_adoptions.md", "benchmark_coco/README.md", "benchmark_nlp/README.md", "benchmark_oid/README.md"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["setup.py", "requirements.txt", "setup_dev_env.sh"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as stale and refresh it.
- If the working tree state or dirty paths change materially, refresh it.
- If the public package version, import names, or public exports change, refresh it.
