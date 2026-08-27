# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-01T09:10:00Z",
  "repository": {
    "name": "FlagEmbedding",
    "remote_url": "https://github.com/FlagOpen/FlagEmbedding",
    "vcs": "git",
    "branch": "master",
    "tag": "v1.4.0",
    "commit": "7ed43d67ec03fbe5c31c0992dbfa941fb1860549",
    "working_tree": "clean-before-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "FlagEmbedding",
      "version": "1.4.0",
      "import_names": ["FlagEmbedding"]
    }
  ],
  "evidence": {
    "source_roots": ["FlagEmbedding"],
    "docs": ["README.md", "docs/source/API", "docs/source/FAQ", "Tutorials"],
    "examples": ["examples/inference", "examples/finetune", "examples/evaluation"],
    "tests": ["tests"],
    "scripts": ["scripts"],
    "configs": ["examples/finetune/ds_stage0.json", "examples/finetune/ds_stage1.json"],
    "excluded_or_limited": ["FlagEmbedding.egg-info", "research", "large benchmark/model/data artifacts", "docs build/static media"]
  }
}
```

The snapshot records the source checkout before generated skill files were
created under `skills/`. Generated skill and review artifacts are not source
evidence dirty paths.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the source checkout has uncommitted changes outside generated skill or
  review-artifact paths, compare those paths with the evidence list and run
  `refresh-repo-skill` when public APIs, docs, examples, scripts, configs, or
  tests changed.
- If package metadata, public imports, model mappings, fine-tuning module entry
  points, evaluation arguments, or optional dependency behavior changed even on
  the same commit, run `refresh-repo-skill`.
