# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
ContextForge. If the current repo commit, package version, public entry points,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:21:55Z",
  "repository": {
    "name": "mcp-context-forge",
    "remote_url": "https://github.com/IBM/mcp-context-forge.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6004d236479c12ed2571d9bf9dc5cc20bf3aead7",
    "working_tree": "clean-before-skill-generation; generated skill files created under skills/ after snapshot",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "mcp-contextforge-gateway",
      "version": "1.0.7",
      "import_names": ["mcpgateway"]
    }
  ],
  "entry_points": {
    "console_scripts": {
      "mcpgateway": "mcpgateway.cli:main",
      "mcpplugins": "cpex.tools.cli:main",
      "cforge": "mcpgateway.tools.cli:main",
      "init-secrets": "mcpgateway.scripts.init_secrets:main",
      "mcpgateway-server": "mcpgateway.__main__:main"
    }
  },
  "evidence": {
    "source_roots": ["mcpgateway/", "crates/mcp_runtime/"],
    "docs": ["README.md", "AGENTS.md", "docs/", "tests/AGENTS.md", "plugins/AGENTS.md", "charts/AGENTS.md", "crates/mcp_runtime/DEVELOPING.md"],
    "examples": ["mcp-servers/", "scripts/demo_a2a_agent.py", "scripts/demo_a2a_agent_auth.py"],
    "tests": ["tests/", "plugins/test_prompt_output_sentinel.py", "plugins/test_tool_output_sentinel.py"],
    "configs": ["pyproject.toml", "Makefile", ".env.example", "plugins/config.yaml", "charts/mcp-stack/", "docker-compose.yml", "Containerfile"]
  },
  "environment_verification": {
    "status": "ok",
    "required_backend": "cpu",
    "distribution_import": "passed",
    "pip_check": "passed",
    "cli_help": ["mcpgateway", "cforge", "init-secrets"]
  },
  "imported_live": false
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale.
- If package metadata, public console scripts, major route families, source root
  layout, or security invariants changed, refresh even if the commit is close.
- If the current checkout is dirty in source, docs, tests, or config paths not
  listed as generated skill output, refresh before relying on detailed guidance.
- If optional backends such as Rust MCP runtime, plugin framework, or RBAC/token
  scoping changed substantially, refresh the owning sub-skill.

## Notes

The repository was clean before generation began. The `skills/` dirty path is
from generated runtime skill and verification artifacts, not from source code
used as evidence.
