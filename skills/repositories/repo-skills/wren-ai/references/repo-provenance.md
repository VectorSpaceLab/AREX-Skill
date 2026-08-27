# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a new WrenAI checkout. If
the commit, working-tree state, package versions, or major evidence surfaces
differ, refresh the skill from the current repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T07:00:00Z",
  "repository": {
    "name": "WrenAI",
    "remote_url": "https://github.com/Canner/WrenAI.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ec85b1e1589ad2b6981d08df1f6b2ad29ae5b902",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/WrenAI.log",
      "skills/tests/"
    ]
  },
  "packages": [
    {
      "name": "wrenai",
      "version": "0.13.2",
      "import_names": ["wren"]
    },
    {
      "name": "wren-core-py",
      "version": "0.7.3",
      "import_names": ["wren_core"]
    },
    {
      "name": "wren-langchain",
      "version": "0.2.1",
      "import_names": ["wren_langchain"]
    },
    {
      "name": "wren-pydantic",
      "version": "0.2.1",
      "import_names": ["wren_pydantic"]
    },
    {
      "name": "@wrenai/wren-core-wasm",
      "version": "0.4.1",
      "import_names": []
    }
  ],
  "evidence": {
    "source_roots": [
      "core/wren/src/wren",
      "core/wren-core/core/src",
      "core/wren-core-base/src",
      "core/wren-core-py/src",
      "core/wren-core-wasm/sdk/src",
      "sdk/wren-langchain/src/wren_langchain",
      "sdk/wren-pydantic/src/wren_pydantic"
    ],
    "docs": ["README.md", "docs/core", "skills"],
    "examples": ["examples/v5-jaffle", "core/wren-core-wasm/examples", "sdk/*/examples"],
    "tests": ["core/wren/tests", "core/wren-core-py/tests", "sdk/*/tests"],
    "configs": ["core/wren/pyproject.toml", "core/wren-core-*/Cargo.toml", "sdk/*/pyproject.toml"]
  }
}
```

The listed dirty paths describe the source snapshot before this generated skill
and its review artifacts were written. They are not runtime dependencies.

## Refresh Check

- If the current Git commit differs, treat this skill as potentially stale.
- If the original dirty paths have changed, inspect the changed public workflow
  before reusing this skill without refresh.
- Refresh when package metadata, CLI command groups, framework toolkit
  signatures, project schema versions, or WASM API surfaces change.
