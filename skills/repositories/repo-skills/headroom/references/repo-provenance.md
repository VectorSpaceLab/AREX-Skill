# Repository Provenance

Read this before deciding whether this skill is current for a checkout of Headroom. If the source commit, dirty state, package metadata, or major evidence paths differ, run the repo-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:30:00Z",
  "repository": {
    "name": "headroom",
    "remote_url": "https://github.com/headroomlabs-ai/headroom.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1a04c957f53ef25ab1209166f425a7876913c4d3",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "headroom-ai",
      "version": "0.34.0",
      "import_names": ["headroom", "headroom._core"]
    },
    {
      "name": "headroom-ai",
      "version": "0.34.0",
      "import_names": ["headroom-ai"],
      "ecosystem": "npm",
      "node_requirement": ">=18.0.0"
    }
  ],
  "evidence": {
    "source_roots": [
      "headroom/",
      "crates/headroom-core/",
      "crates/headroom-proxy/",
      "crates/headroom-py/",
      "sdk/typescript/"
    ],
    "docs": ["README.md", "docs/", "llms.txt"],
    "examples": ["examples/", "sdk/typescript/examples/"],
    "tests": ["tests/", "crates/headroom-core/tests/", "crates/headroom-proxy/tests/", "sdk/typescript/test/"],
    "configs": ["pyproject.toml", "Cargo.toml", "sdk/typescript/package.json", "headroom/paths.py", "headroom/install/paths.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `1a04c957f53ef25ab1209166f425a7876913c4d3`, treat this skill as potentially stale.
- The checkout was clean before generation; the current `skills/` dirty path is generated output and review artifacts, not source evidence.
- If `pyproject.toml`, `Cargo.toml`, `sdk/typescript/package.json`, the CLI command tree, public provider routes, memory API, or compression signatures change, refresh the skill even if the commit remains unchanged in a rebased checkout.
