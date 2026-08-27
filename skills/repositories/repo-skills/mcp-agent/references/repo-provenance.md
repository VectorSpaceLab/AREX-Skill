# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T00:00:00Z",
  "repository": {
    "name": "mcp-agent",
    "remote_url": "https://github.com/lastmile-ai/mcp-agent",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f62d849350816588b1c6294e7914bbe4d8b84072",
    "working_tree": "dirty-disco-generated-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "mcp-agent",
      "version": "0.2.6",
      "import_names": ["mcp_agent"]
    }
  ],
  "entry_points": {
    "console_scripts": ["silsila", "mcp-agent", "mcp-cloud", "mcpc"]
  },
  "evidence": {
    "source_roots": ["src/mcp_agent"],
    "docs": ["README.md", "LLMS.txt", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "schema/mcp-agent.config.schema.json"],
    "scripts": ["scripts"]
  }
}
```

## Evidence Summary

- `pyproject.toml` defined package metadata, base dependencies, optional extras, Python requirement, and console scripts.
- `src/mcp_agent/` provided verified APIs for app lifecycle, agents, workflows, MCP integration, CLI, Temporal execution, logging/tracing, OAuth, and adapters.
- `README.md`, `LLMS.txt`, and `docs/` provided public workflows, configuration, CLI, cloud, Temporal, observability, and MCP guidance.
- `examples/` provided real user workflows; the generated skill distills or adapts them into bundled references/scripts instead of requiring the examples directory.
- `tests/` provided behavior and edge-case evidence for candidate native verification.
- `scripts/` provided source utilities that were adapted, documented as reference-only, or excluded in the integration artifacts.

## Refresh Check

Run `refresh-repo-skill` when any of these are true:

- The current checkout commit differs from `f62d849350816588b1c6294e7914bbe4d8b84072`.
- The package version, optional extras, CLI entry points, config schema, or public imports differ from this snapshot.
- The current dirty tree contains source/docs/examples/tests/config changes beyond DisCo-generated `skills/` output.
- Major docs, examples, workflow APIs, server/auth behavior, Temporal executor behavior, or CLI commands changed.

This provenance intentionally omits local environment prefixes, Python executable paths, cache paths, and inspection-machine details.
