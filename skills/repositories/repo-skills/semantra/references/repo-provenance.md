# Repository Provenance

## Purpose

Read this before deciding whether this Semantra repo skill is current for a
checkout of the repository. If the current repo commit, dirty state, package
version, public entry points, or major evidence paths differ from this snapshot,
run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T12:48:21Z",
  "repository": {
    "name": "semantra-python",
    "remote_url": "https://github.com/freedmand/semantra-python.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1aed8fd0057f6b3eb7946e0f351f9c668842774d",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": [
      "skills/disco/semantra/"
    ]
  },
  "packages": [
    {
      "name": "semantra",
      "version": "0.1.12",
      "import_names": ["semantra"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/semantra",
      "client/src"
    ],
    "docs": [
      "README.md",
      "docs/tutorial.md",
      "docs/lesson_1_semantically_searching_shakespeare.md",
      "docs/lesson_2_advanced_searching.md",
      "docs/guide_models.md",
      "docs/guide_openai.md",
      "docs/concept_embeddings.md",
      "docs/concept_windows.md",
      "docs/help.md"
    ],
    "examples": [
      "docs/example_docs"
    ],
    "tests": [
      "client/src/layoutEngine.test.ts"
    ],
    "configs": [
      "pyproject.toml",
      "client/package.json"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, config, or package-data changes
  outside generated skill/review artifacts, run `refresh-repo-skill`.
- If Semantra's package metadata, console entry point, dependency bounds, model
  registry, Flask routes, cache artifact schema, or web query parser changed,
  run `refresh-repo-skill`.
- If only generated skill files changed during verification, update review
  artifacts instead of treating the upstream package as stale.
