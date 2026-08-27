# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MarkItDown. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T17:32:35Z",
  "repository": {
    "name": "markitdown",
    "remote_url": "https://github.com/microsoft/markitdown",
    "vcs": "git",
    "branch": "main",
    "tag": "v0.1.6",
    "commit": "e144e0a2be95b34df17433bac904e635f2c5e551",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "markitdown",
      "version": "0.1.6",
      "import_names": ["markitdown"],
      "entry_points": ["markitdown"]
    },
    {
      "name": "markitdown-mcp",
      "version": "0.0.1a5",
      "import_names": ["markitdown_mcp"],
      "entry_points": ["markitdown-mcp"]
    },
    {
      "name": "markitdown-ocr",
      "version": "0.1.0",
      "import_names": ["markitdown_ocr"],
      "entry_points": ["markitdown.plugin:ocr"]
    },
    {
      "name": "markitdown-sample-plugin",
      "version": "0.1.0a1",
      "import_names": ["markitdown_sample_plugin"],
      "entry_points": ["markitdown.plugin:sample_plugin"]
    }
  ],
  "evidence": {
    "source_roots": [
      "packages/markitdown/src/markitdown",
      "packages/markitdown-mcp/src/markitdown_mcp",
      "packages/markitdown-ocr/src/markitdown_ocr",
      "packages/markitdown-sample-plugin/src/markitdown_sample_plugin"
    ],
    "docs": [
      "README.md",
      "packages/markitdown/README.md",
      "packages/markitdown-mcp/README.md",
      "packages/markitdown-ocr/README.md",
      "packages/markitdown-sample-plugin/README.md"
    ],
    "package_metadata": [
      "packages/markitdown/pyproject.toml",
      "packages/markitdown-mcp/pyproject.toml",
      "packages/markitdown-ocr/pyproject.toml",
      "packages/markitdown-sample-plugin/pyproject.toml"
    ],
    "tests": [
      "packages/markitdown/tests",
      "packages/markitdown-ocr/tests",
      "packages/markitdown-sample-plugin/tests"
    ],
    "deployment": [
      "packages/markitdown-mcp/Dockerfile"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or if dirty paths differ from this snapshot, run `refresh-repo-skill`.
- If any package version, optional dependency group, console script, plugin entry point, converter signature, or MCP transport behavior changed, run `refresh-repo-skill`.
- If new user-facing packages, plugins, converters, examples, or tests were added under `packages/`, run `refresh-repo-skill` or `extend-repo-skill` depending on whether existing coverage is stale or merely incomplete.
