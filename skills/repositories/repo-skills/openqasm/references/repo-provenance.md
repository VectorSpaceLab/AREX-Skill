# Repository Provenance

## Purpose

Read this before deciding whether the `openqasm` skill still matches a
checkout. If the commit, dirty state, package metadata, public entry points, or
major evidence paths differ, run the repository-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T18:48:45Z",
  "repository": {
    "name": "openqasm",
    "remote_url": "https://github.com/openqasm/openqasm.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7fbf9e9eb3692a1288c014d6efd43523701886c6",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "openqasm3",
      "version": "1.0.1",
      "import_names": ["openqasm3"]
    },
    {
      "name": "openqasm_reference_parser",
      "version": null,
      "import_names": ["openqasm_reference_parser"]
    }
  ],
  "evidence": {
    "source_roots": [
      "source/openqasm/openqasm3",
      "source/grammar/qasm3Lexer.g4",
      "source/grammar/qasm3Parser.g4"
    ],
    "docs": [
      "README.md",
      "source/intro.rst",
      "source/language",
      "source/openqasm/README.md",
      "source/openqasm/docs/api"
    ],
    "examples": ["examples"],
    "tests": ["source/openqasm/tests", "source/grammar/tests"],
    "configs": [
      "source/openqasm/setup.cfg",
      "source/openqasm/pyproject.toml",
      "source/openqasm/ANTLR_VERSIONS.txt",
      "source/grammar/setup.cfg",
      "source/grammar/pyproject.toml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and refresh it.
- If the checkout's dirty state or changed relative paths differ from the
  snapshot, refresh before making source-specific claims.
- Refresh if `openqasm3` changes its public entry points, parser extra,
  supported language versions, AST node families, printer behavior, or ANTLR
  compatibility range.
- The published distribution version alone is not a sufficient freshness key:
  the current source can change while retaining package version `1.0.1`.
