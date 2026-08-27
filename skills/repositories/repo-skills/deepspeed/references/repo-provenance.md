# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DeepSpeed. If the current repo commit, dirty state, package version, public APIs, docs, examples, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "DeepSpeed",
    "remote_url": "https://github.com/deepspeedai/DeepSpeed.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ad026a1fd1239071f2afb0a9c07f04b3cd732e02",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "deepspeed",
      "version": "0.19.3+ad026a1",
      "import_names": ["deepspeed"]
    }
  ],
  "evidence": {
    "source_roots": ["deepspeed", "accelerator", "op_builder", "csrc"],
    "docs": ["README.md", "docs/_tutorials", "docs/_pages", "docs/code-docs/source"],
    "examples": ["examples/sdma_allgather"],
    "tests": ["tests/unit", "tests/hybrid_engine"],
    "scripts": ["bin", "scripts"],
    "metadata": ["setup.py", "setup.cfg", "requirements"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the source checkout has dirty paths outside the generated `skills/` tree, compare them with the evidence paths and refresh when public behavior changed.
- If package metadata, installed scripts, config fields, or public entry points changed even on the same commit, run `refresh-skill-from-repo`.
- If DeepSpeed docs add or remove major workflow pages for training, inference, parallelism, ops, or tooling, refresh the affected sub-skills.
