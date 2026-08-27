# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "graphrag",
    "remote_url": "https://github.com/microsoft/graphrag.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6d02c2355c3fed4c49007572fbe951d73258a37f",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "No pre-existing source modifications were observed during evidence collection; the dirty path is the generated DisCo output."
  },
  "packages": [
    {"name": "graphrag", "version": "3.1.0", "import_names": ["graphrag"]},
    {"name": "graphrag-cache", "version": "3.1.0", "import_names": ["graphrag_cache"]},
    {"name": "graphrag-chunking", "version": "3.1.0", "import_names": ["graphrag_chunking"]},
    {"name": "graphrag-common", "version": "3.1.0", "import_names": ["graphrag_common"]},
    {"name": "graphrag-input", "version": "3.1.0", "import_names": ["graphrag_input"]},
    {"name": "graphrag-llm", "version": "3.1.0", "import_names": ["graphrag_llm"]},
    {"name": "graphrag-storage", "version": "3.1.0", "import_names": ["graphrag_storage"]},
    {"name": "graphrag-vectors", "version": "3.1.0", "import_names": ["graphrag_vectors"]}
  ],
  "evidence": {
    "source_roots": [
      "packages/graphrag/graphrag",
      "packages/graphrag-cache/graphrag_cache",
      "packages/graphrag-chunking/graphrag_chunking",
      "packages/graphrag-common/graphrag_common",
      "packages/graphrag-input/graphrag_input",
      "packages/graphrag-llm/graphrag_llm",
      "packages/graphrag-storage/graphrag_storage",
      "packages/graphrag-vectors/graphrag_vectors"
    ],
    "docs": [
      "README.md",
      "docs/get_started.md",
      "docs/cli.md",
      "docs/config",
      "docs/index",
      "docs/query",
      "docs/prompt_tuning"
    ],
    "examples": [
      "docs/examples_notebooks"
    ],
    "tests": [
      "tests/unit",
      "tests/verbs",
      "tests/smoke",
      "tests/integration"
    ],
    "configs": [
      "pyproject.toml",
      "packages/*/pyproject.toml",
      "mkdocs.yaml"
    ],
    "excluded": [
      "unified-search-app",
      "scripts/copy_build_assets.py",
      "scripts/update_workspace_dependency_versions.py",
      "scripts/semver-check.sh",
      "scripts/spellcheck.sh",
      "generated caches and build outputs"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-skill-from-repo`.
- If package metadata, public CLI commands, API signatures, config models, or output table contracts changed, refresh even on the same commit.
- If a current checkout has source changes outside generated skill artifacts, compare those paths against the evidence map and refresh when they touch public behavior.
