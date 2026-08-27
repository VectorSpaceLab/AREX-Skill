# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Superduper repository. If the current repo commit, dirty state, package version, plugin exports, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T16:37:22Z",
  "repository": {
    "name": "superduper",
    "remote_url": "https://github.com/superduper-io/superduper.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6d192e7bf255f913b445a44dc9486e7013ddc6bc",
    "working_tree": "clean",
    "dirty_paths": [],
    "note": "Source evidence was captured from a clean checkout before generated skill artifacts were added under skills/."
  },
  "packages": [
    {
      "name": "superduper-framework",
      "version": "0.7.3",
      "import_names": ["superduper"]
    },
    {
      "name": "superduper_mongodb",
      "version": "0.9.1",
      "import_names": ["superduper_mongodb"],
      "verification": "optional first-party plugin used for local mongomock smoke"
    },
    {
      "name": "first-party plugin packages",
      "version": "source pyproject/__init__ versions vary",
      "import_names": [
        "superduper_sql",
        "superduper_snowflake",
        "superduper_redis",
        "superduper_chromadb",
        "superduper_lance",
        "superduper_qdrant",
        "superduper_openai",
        "superduper_anthropic",
        "superduper_cohere",
        "superduper_jina",
        "superduper_llamacpp",
        "superduper_vllm",
        "superduper_sentence_transformers",
        "superduper_transformers",
        "superduper_torch",
        "superduper_sklearn",
        "superduper_pillow",
        "superduper_template"
      ],
      "verification": "cataloged from source metadata; not all optional plugins were installed"
    }
  ],
  "evidence": {
    "metadata": ["pyproject.toml", "MANIFEST.in", "README.md"],
    "source_roots": ["superduper/"],
    "plugin_sources": ["plugins/"],
    "examples": ["applications/simple_rag/"],
    "tests": ["test/unittest/", "test/integration/", "test/utils/", "test/configs/"],
    "ci": [".github/workflows/ci_code.yml", ".github/workflows/ci_plugins.yaml"],
    "existing_skills": ["skills/superduper.log"]
  },
  "known_snapshot_warnings": [
    "The declared console script points to superduper.__main__:run, but this checkout has no superduper/__main__.py.",
    "The generated skill verifies core Python API plus local mongomock backend smoke; optional cloud/API/GPU/service plugin runtime paths are documented but not required backend gates."
  ]
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public exports, plugin pyprojects, or URI routing changes even on the same commit, run `refresh-repo-skill`.
- If a later version adds `superduper.__main__` or changes CLI behavior, refresh before giving CLI instructions.
- If a task requires optional plugin runtime behavior that was not verified here, install and verify that plugin/backend in the target environment before relying on the catalog as more than install/import guidance.
