# Repository Provenance

## Purpose

Read this before deciding whether this Langroid repo skill is current for a
checkout or installed distribution. If the current commit, package version, or
major evidence layout differs from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:13:02Z",
  "repository": {
    "name": "langroid",
    "remote_url": "https://github.com/langroid/langroid.git",
    "vcs": "git",
    "branch": "main",
    "tag": "0.65.16",
    "commit": "786c4fe39a3fd7b595d3220a08676e9af78f4143",
    "working_tree": "clean-at-evidence-capture",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "langroid",
      "version": "0.65.16",
      "import_names": ["langroid"]
    }
  ],
  "evidence": {
    "source_roots": ["langroid"],
    "docs": ["README.md", "docs/quick-start", "docs/tutorials", "docs/notes", "docs/examples"],
    "examples": ["examples/basic", "examples/docqa", "examples/data-qa", "examples/kg-chat", "examples/mcp", "examples/chainlit", "examples/portkey", "examples/langdb", "examples/privacy", "examples/reasoning"],
    "tests": ["tests/main", "tests/extras"],
    "configs": ["pyproject.toml", "pytest.ini", "Makefile", "CLAUDE.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If the installed `langroid` distribution version differs from `0.65.16`,
  verify whether public APIs and optional extras changed.
- If public files under `langroid/`, `docs/`, `examples/`, `tests/`, or
  `pyproject.toml` changed materially, refresh this skill.
- Generated skill output under a checkout-local `skills/` directory was not used
  as source evidence and does not by itself mean the upstream package changed.
