# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package metadata, or major
evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:42:04Z",
  "repository": {
    "name": "hifi-gan",
    "remote_url": "https://github.com/jik876/hifi-gan.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4769534d45265d52a904b850da5a622601885777",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "hifi-gan",
      "version": null,
      "import_names": ["env", "meldataset", "models", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["."],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["config_v1.json", "config_v2.json", "config_v3.json", "requirements.txt"],
    "data": ["LJSpeech-1.1/training.txt", "LJSpeech-1.1/validation.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and refresh it.
- If the working tree dirty paths change in a meaningful way, refresh the
  skill.
- If package metadata or public entry points change on the same commit,
  refresh the skill.
