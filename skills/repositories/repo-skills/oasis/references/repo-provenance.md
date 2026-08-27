# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the OASIS repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:37:48Z",
  "repository": {
    "name": "oasis",
    "remote_url": "https://github.com/camel-ai/oasis.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2048ee6dd8d2a9e62f53773f00200ef51a086468",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "camel-oasis",
      "version": "0.2.5",
      "import_names": ["oasis"]
    }
  ],
  "evidence": {
    "source_roots": ["oasis"],
    "docs": [
      "README.md",
      "docs/key_modules",
      "docs/simulation",
      "docs/user_generation",
      "docs/visualization",
      "docs/cookbooks"
    ],
    "examples": [
      "examples/*.py",
      "examples/experiment"
    ],
    "tests": [
      "test/agent",
      "test/infra/database",
      "test/infra/recsys"
    ],
    "configs_and_data": [
      "pyproject.toml",
      "oasis/social_platform/schema",
      "data/reddit/user_data_36.json",
      "data/twitter_dataset"
    ],
    "supporting_reference_only": [
      "generator",
      "visualization"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the source working tree is dirty before generated skill outputs are considered, run `refresh-repo-skill` or inspect whether the changed files affect public APIs, docs, examples, tests, or schemas.
- If package metadata, public exports, environment signatures, action names, schema tables, or example workflows changed even on the same commit, run `refresh-repo-skill`.
- If a task depends on optional TwHIN, VLLM, Neo4j, OpenAI embedding, or large-experiment behavior that was not verified for this snapshot, treat that specific backend as needing fresh task-scoped verification.
