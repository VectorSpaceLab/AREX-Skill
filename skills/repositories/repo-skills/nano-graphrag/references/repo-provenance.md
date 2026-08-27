# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:56:03Z",
  "repository": {
    "name": "nano-graphrag",
    "remote_url": "https://github.com/gusye1234/nano-graphrag.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "acb35c065614eb5a2f5f1be9a56b235f5a2e0a7a",
    "working_tree": "clean before generated skill artifacts were written",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "nano-graphrag",
      "version": "0.0.8.2",
      "import_names": ["nano_graphrag"]
    }
  ],
  "evidence": {
    "source_roots": ["nano_graphrag"],
    "docs": ["readme.md", "docs/FAQ.md", "docs/use_neo4j_for_graphrag.md", "docs/benchmark-en.md", "docs/benchmark-zh.md", "docs/benchmark-dspy-entity-extraction.md"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": [".env.example.azure", "setup.py", "requirements.txt", "requirements-dev.txt"],
    "existing_repo_local_skills": ["skills/nano-graphrag.log"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
- If the current checkout contains generated skill or review artifacts under `skills/`, do not treat those artifacts alone as source evidence changes; compare source, docs, examples, tests, and package metadata paths first.
- If the current code no longer imports `transformers.AutoTokenizer` at package import time, update install troubleshooting because this skill records that caveat for version `0.0.8.2`.
