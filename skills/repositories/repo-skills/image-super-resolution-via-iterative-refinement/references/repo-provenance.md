# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, public scripts, configs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:35:01Z",
  "repository": {
    "name": "Image-Super-Resolution-via-Iterative-Refinement",
    "remote_url": "https://github.com/Janspiry/Image-Super-Resolution-via-Iterative-Refinement.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "01d27a7cbfa8502be1d8dbd4ee02fcbd5e44389d",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["core", "data", "model"]
    }
  ],
  "evidence": {
    "source_roots": ["core", "data", "model"],
    "docs": ["README.md"],
    "examples": ["config", "misc"],
    "tests": [],
    "configs": ["config/sample_ddpm_128.json", "config/sample_sr3_128.json", "config/sr_ddpm_16_128.json", "config/sr_sr3_16_128.json", "config/sr_sr3_64_512.json"],
    "scripts": ["data/prepare_data.py", "sr.py", "sample.py", "infer.py", "eval.py"],
    "requirements": ["requirement.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source, config, or public script files changed even on the same commit, refresh the skill.
- Ignore differences caused only by regenerated skill artifacts under `skills/` unless the generated skill itself is the target of review.
- If packaging metadata is later added to the repository, refresh the installation and import guidance.
